"""
FloodGuard — proactive rate-limiting middleware for Telethon.

Telethon already handles ``FloodWaitError`` by sleeping and retrying, but
that happens *reactively* after Telegram has already rejected the request.
Repeated flood waits can get the account flagged or temporarily restricted.

``FloodGuard`` sits **in front** of the RPC layer and proactively throttles
outgoing calls so that Telegram is less likely to issue flood errors in the
first place.

How it works
------------

Each TL method type (e.g. ``SendMessageRequest``) is tracked in a sliding
time window.  When the number of calls in the window exceeds the configured
threshold, the guard sleeps for the remaining window time before allowing the
call through.

You can configure global limits, per-method limits, or combine both.

Usage
-----

.. code-block:: python

    from telethon import TelegramClient
    from telethon.contrib.floodguard import FloodGuard, MethodLimit

    client = TelegramClient(...)

    guard = FloodGuard(
        client,
        # Global: at most 20 any-method calls per 10 seconds
        max_calls=20,
        per_seconds=10,
        # Per-method overrides
        method_limits=[
            MethodLimit('SendMessageRequest', max_calls=5, per_seconds=5),
            MethodLimit('ForwardMessagesRequest', max_calls=3, per_seconds=10),
        ],
    )

    # attach — done once, before client.start() / connect()
    guard.attach()

    async with client:
        await client.run_until_disconnected()

Thread safety
-------------
``FloodGuard`` is async-safe for a single event loop (asyncio).
It is **not** safe to share across multiple running event loops.
"""

from __future__ import annotations

import asyncio
import collections
import logging
import time
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from ..client.telegramclient import TelegramClient

_log = logging.getLogger(__name__)


@dataclass
class MethodLimit:
    """Per-method rate-limit configuration."""
    method: str           # TL class name, e.g. 'SendMessageRequest'
    max_calls: int        # max calls within per_seconds
    per_seconds: float    # sliding-window width in seconds


class _WindowedCounter:
    """Tracks call timestamps in a sliding time window."""

    def __init__(self, per_seconds: float):
        self._window = per_seconds
        self._timestamps: Deque[float] = collections.deque()

    def record(self, ts: float) -> None:
        self._purge(ts)
        self._timestamps.append(ts)

    def count(self, ts: float) -> int:
        self._purge(ts)
        return len(self._timestamps)

    def oldest(self) -> Optional[float]:
        return self._timestamps[0] if self._timestamps else None

    def _purge(self, ts: float) -> None:
        cutoff = ts - self._window
        while self._timestamps and self._timestamps[0] <= cutoff:
            self._timestamps.popleft()


class FloodGuard:
    """
    Proactive rate-limiter that wraps ``TelegramClient.__call__``.

    Parameters
    ----------
    client:
        The :class:`TelegramClient` to guard.
    max_calls:
        Maximum number of *any* RPC calls in ``per_seconds``.
        Set to ``None`` to disable the global limit.
    per_seconds:
        Sliding-window width for the global limit (default: ``10``).
    method_limits:
        Optional list of :class:`MethodLimit` objects for per-method overrides.
    on_throttle:
        Optional async callable ``async (method_name, sleep_seconds) -> None``
        called whenever the guard introduces a delay.
    """

    def __init__(
        self,
        client: 'TelegramClient',
        *,
        max_calls: Optional[int] = 30,
        per_seconds: float = 10.0,
        method_limits: Optional[List[MethodLimit]] = None,
        on_throttle=None,
    ):
        self._client = client
        self._max_calls = max_calls
        self._per_seconds = per_seconds
        self._on_throttle = on_throttle

        # Global counter
        self._global: Optional[_WindowedCounter] = (
            _WindowedCounter(per_seconds) if max_calls is not None else None
        )

        # Per-method counters + limits
        self._method_limits: Dict[str, Tuple[int, _WindowedCounter]] = {}
        for ml in (method_limits or []):
            self._method_limits[ml.method] = (
                ml.max_calls,
                _WindowedCounter(ml.per_seconds),
            )

        self._attached = False
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def attach(self) -> 'FloodGuard':
        """
        Install the guard on the client.  Call this once before connecting.

        Returns ``self`` for chaining.
        """
        if self._attached:
            return self

        client = self._client
        guard = self

        _orig_call = client.__class__.__call__

        async def _guarded_call(self_c, *args, **kwargs):
            request = args[0] if args else None
            method = type(request).__name__ if request is not None else 'unknown'
            await guard._maybe_throttle(method)
            return await _orig_call(self_c, *args, **kwargs)

        client.__class__.__call__ = _guarded_call
        self._attached = True
        _log.debug('FloodGuard attached to client %r', client)
        return self

    def detach(self) -> 'FloodGuard':
        """
        Remove the guard from the client (restores the original ``__call__``).
        """
        if not self._attached:
            return self
        # We cannot easily un-wrap the patched method without storing the
        # original. For now, raise so the user knows this is a limitation.
        raise NotImplementedError(
            'FloodGuard.detach() is not yet implemented. '
            'Create a new TelegramClient instance to remove the guard.'
        )

    # ------------------------------------------------------------------
    # Internal throttle logic
    # ------------------------------------------------------------------

    async def _maybe_throttle(self, method: str) -> None:
        async with self._lock:
            now = time.monotonic()
            sleep_s = self._compute_sleep(method, now)
            if sleep_s > 0:
                _log.debug(
                    'FloodGuard: throttling %s for %.2fs', method, sleep_s
                )
                if self._on_throttle:
                    await self._on_throttle(method, sleep_s)
            # Record *after* potential sleep so timestamps are accurate
        if sleep_s > 0:
            await asyncio.sleep(sleep_s)
        # Re-acquire lock to record the call
        async with self._lock:
            now2 = time.monotonic()
            if self._global is not None:
                self._global.record(now2)
            if method in self._method_limits:
                _, counter = self._method_limits[method]
                counter.record(now2)

    def _compute_sleep(self, method: str, now: float) -> float:
        """Return seconds to sleep before allowing this call; 0 if no wait needed."""
        waits = []

        if self._global is not None:
            cnt = self._global.count(now)
            if cnt >= self._max_calls:
                oldest = self._global.oldest()
                if oldest is not None:
                    waits.append(
                        (oldest + self._global._window) - now
                    )

        if method in self._method_limits:
            max_c, counter = self._method_limits[method]
            cnt = counter.count(now)
            if cnt >= max_c:
                oldest = counter.oldest()
                if oldest is not None:
                    waits.append((oldest + counter._window) - now)

        return max(waits) if waits else 0.0

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        status = 'attached' if self._attached else 'not attached'
        return (
            f'<FloodGuard {status} global={self._max_calls}/{self._per_seconds}s '
            f'methods={list(self._method_limits)}>'
        )
