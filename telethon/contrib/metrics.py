"""
Prometheus metrics for Telethon clients.

Exposes an HTTP ``/metrics`` endpoint in Prometheus text format.
Tracks RPC calls, flood waits, reconnects, and update queue depth.

Requirements
------------
This module is **optional**.  Install the extra dependency if you want it::

    pip install prometheus_client

If ``prometheus_client`` is not installed the module still imports cleanly
and all public symbols are no-ops / stubs – so you can always
``from telethon.contrib.metrics import TelethonMetrics`` without a hard dep.

Usage
-----
.. code-block:: python

    from telethon import TelegramClient
    from telethon.contrib.metrics import TelethonMetrics

    client = TelegramClient(...)
    metrics = TelethonMetrics(client)       # attach to existing client

    # Start the HTTP server
    await metrics.start_server(port=9090)

    async with client:
        await client.run_until_disconnected()

Metrics exposed
---------------
``telethon_rpc_calls_total{method}``
    Counter. Total RPC calls sent, labelled by TL type name.

``telethon_rpc_errors_total{method,error}``
    Counter. Total RPC errors by method and error class name.

``telethon_flood_waits_total{method}``
    Counter. FloodWaitErrors triggered, labelled by method.

``telethon_flood_wait_seconds_total{method}``
    Counter. Cumulative seconds spent waiting due to flood wait.

``telethon_reconnects_total``
    Counter. Number of MTProto reconnection events.

``telethon_updates_queue_depth``
    Gauge. Current depth of the internal updates asyncio queue.

``telethon_connected``
    Gauge. 1 if the client is currently connected, 0 otherwise.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..client.telegramclient import TelegramClient

_log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Try to import prometheus_client; fall back to stubs if unavailable
# ---------------------------------------------------------------------------
try:
    import prometheus_client as prom
    from prometheus_client import Counter, Gauge, start_http_server as _prom_start_http_server

    _PROMETHEUS_AVAILABLE = True
except ImportError:
    _PROMETHEUS_AVAILABLE = False
    prom = None  # type: ignore[assignment]

    class _Stub:  # pragma: no cover
        def labels(self, **_kw):
            return self
        def inc(self, _n=1): pass
        def set(self, _v): pass
        def observe(self, _v): pass

    class Counter(_Stub):  # type: ignore[no-redef]
        def __init__(self, *a, **kw): pass

    class Gauge(_Stub):  # type: ignore[no-redef]
        def __init__(self, *a, **kw): pass

    def _prom_start_http_server(*a, **kw):  # type: ignore[misc]
        raise RuntimeError('prometheus_client is not installed. Run: pip install prometheus_client')


class TelethonMetrics:
    """
    Attaches Prometheus instrumentation to a :class:`TelegramClient`.

    Hooks into the client's ``__call__`` (RPC invocation), flood-wait
    retry logic, and the MTProto reconnect callback.

    Parameters
    ----------
    client:
        The :class:`TelegramClient` to instrument.
    namespace:
        Prefix for all metric names (default ``'telethon'``).
    registry:
        Prometheus registry to use (defaults to the global default registry).
    """

    def __init__(
        self,
        client: 'TelegramClient',
        *,
        namespace: str = 'telethon',
        registry=None,
    ):
        self._client = client
        self._ns = namespace
        reg_kw = {'registry': registry} if registry is not None else {}

        self.rpc_calls = Counter(
            f'{namespace}_rpc_calls_total',
            'Total RPC calls sent',
            ['method'],
            **reg_kw,
        )
        self.rpc_errors = Counter(
            f'{namespace}_rpc_errors_total',
            'Total RPC errors',
            ['method', 'error'],
            **reg_kw,
        )
        self.flood_waits = Counter(
            f'{namespace}_flood_waits_total',
            'FloodWaitErrors triggered',
            ['method'],
            **reg_kw,
        )
        self.flood_wait_seconds = Counter(
            f'{namespace}_flood_wait_seconds_total',
            'Cumulative seconds spent in flood-wait sleep',
            ['method'],
            **reg_kw,
        )
        self.reconnects = Counter(
            f'{namespace}_reconnects_total',
            'MTProto reconnection events',
            **reg_kw,
        )
        self.queue_depth = Gauge(
            f'{namespace}_updates_queue_depth',
            'Current depth of the internal updates asyncio queue',
            **reg_kw,
        )
        self.connected = Gauge(
            f'{namespace}_connected',
            '1 if client is connected, 0 otherwise',
            **reg_kw,
        )

        self._attach()

    # ------------------------------------------------------------------
    # Attachment / hooking
    # ------------------------------------------------------------------

    def _attach(self) -> None:
        """Monkey-patch the client to intercept RPC calls."""
        client = self._client
        metrics = self

        # --- wrap __call__ -------------------------------------------
        _orig_call = client.__class__.__call__

        async def _instrumented_call(self_c, *args, **kwargs):
            request = args[0] if args else None
            method = type(request).__name__ if request is not None else 'unknown'
            metrics.rpc_calls.labels(method=method).inc()
            t0 = time.monotonic()
            try:
                return await _orig_call(self_c, *args, **kwargs)
            except Exception as exc:
                error = type(exc).__name__
                metrics.rpc_errors.labels(method=method, error=error).inc()
                # Track flood waits specifically
                if error == 'FloodWaitError':
                    seconds = getattr(exc, 'seconds', 0) or 0
                    metrics.flood_waits.labels(method=method).inc()
                    metrics.flood_wait_seconds.labels(method=method).inc(seconds)
                raise

        client.__class__.__call__ = _instrumented_call

        # --- reconnect counter ----------------------------------------
        try:
            sender = client._sender
            _orig_reconnect = getattr(sender, 'auto_reconnect_callback', None)

            def _on_reconnect():
                metrics.reconnects.inc()
                if callable(_orig_reconnect):
                    _orig_reconnect()

            sender.auto_reconnect_callback = _on_reconnect
        except AttributeError:
            pass  # sender not yet initialised; reconnect counter will just stay 0

        _log.debug('TelethonMetrics attached to client %r', client)

    # ------------------------------------------------------------------
    # Background gauge updater
    # ------------------------------------------------------------------

    async def _update_gauges_loop(self) -> None:
        """Continuously refreshes queue_depth and connected gauges."""
        while True:
            try:
                if hasattr(self._client, '_updates_queue'):
                    self.queue_depth.set(self._client._updates_queue.qsize())
                self.connected.set(1 if self._client.is_connected() else 0)
            except Exception:  # pragma: no cover
                pass
            await asyncio.sleep(5)

    # ------------------------------------------------------------------
    # HTTP server
    # ------------------------------------------------------------------

    async def start_server(self, port: int = 9090, addr: str = '0.0.0.0') -> None:
        """
        Start the Prometheus HTTP metrics server on ``addr:port``.

        Also starts the background gauge-refresh task.

        Args:
            port: TCP port to listen on (default ``9090``).
            addr: Bind address (default ``'0.0.0.0'``).
        """
        if not _PROMETHEUS_AVAILABLE:
            raise RuntimeError(
                'prometheus_client is not installed. '
                'Install it with: pip install prometheus_client'
            )
        _prom_start_http_server(port, addr=addr)
        _log.info('Prometheus metrics server started on %s:%d', addr, port)
        asyncio.get_event_loop().create_task(self._update_gauges_loop())
