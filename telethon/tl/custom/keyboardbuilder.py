"""
Fluent keyboard builder DSL for Telethon.

Instead of constructing nested lists of Button objects manually, you can
use :class:`Keyboard` as a builder:

.. code-block:: python

    from telethon import Button
    from telethon.tl.custom.keyboardbuilder import Keyboard

    markup = (
        Keyboard()
        .row(Button.inline('Yes ✅', b'yes'), Button.inline('No ❌', b'no'))
        .row(Button.url('Docs', 'https://docs.example.com'))
        .build()
    )

    await client.send_message(chat, 'Pick one:', buttons=markup)

You may also mix ``row()`` and ``add()`` calls:

.. code-block:: python

    kb = Keyboard()
    for i, item in enumerate(items):
        kb.add(Button.inline(item, str(i).encode()))
        if (i + 1) % 3 == 0:          # 3 buttons per row
            kb.end_row()
    markup = kb.build()
"""

from .button import Button


class Keyboard:
    """
    Fluent builder for Telegram reply/inline keyboard markup.

    All methods return ``self`` to allow chaining.
    """

    def __init__(self):
        self._rows: list = []           # list of rows; each row is a list of Button/TL objects
        self._current_row: list = []    # buttons being accumulated for the next row

    # ------------------------------------------------------------------
    # Row-level builders
    # ------------------------------------------------------------------

    def row(self, *buttons) -> 'Keyboard':
        """
        Append a complete row of buttons at once.

        .. code-block:: python

            kb.row(Button.inline('A', b'a'), Button.inline('B', b'b'))
        """
        if self._current_row:
            # Flush any in-progress row first
            self._rows.append(list(self._current_row))
            self._current_row = []

        self._rows.append(list(buttons))
        return self

    def add(self, *buttons) -> 'Keyboard':
        """
        Add one or more buttons to the *current* row without closing it.

        .. code-block:: python

            kb.add(Button.inline('First')).add(Button.inline('Second')).end_row()
        """
        self._current_row.extend(buttons)
        return self

    def end_row(self) -> 'Keyboard':
        """
        Close the current in-progress row and start a new empty one.
        """
        if self._current_row:
            self._rows.append(list(self._current_row))
            self._current_row = []
        return self

    # ------------------------------------------------------------------
    # Preset layouts
    # ------------------------------------------------------------------

    def columns(self, buttons, *, cols: int = 2) -> 'Keyboard':
        """
        Lay out a flat list of buttons in a grid with ``cols`` columns.

        .. code-block:: python

            items = [Button.inline(str(n), str(n).encode()) for n in range(6)]
            kb.columns(items, cols=3)
            # Produces:
            # [0] [1] [2]
            # [3] [4] [5]
        """
        row = []
        for i, btn in enumerate(buttons):
            row.append(btn)
            if len(row) == cols:
                self._rows.append(row)
                row = []
        if row:
            self._rows.append(row)
        return self

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build(self) -> list:
        """
        Return the nested ``[[Button, ...], ...]`` list that you can pass
        directly to ``send_message(buttons=...)``.

        The builder is left intact so you can call ``build()`` multiple
        times (e.g. to send the same keyboard to several chats).
        """
        rows = list(self._rows)
        if self._current_row:
            rows.append(list(self._current_row))
        return rows

    # ------------------------------------------------------------------
    # Convenience shortcuts — thin wrappers around Button class methods
    # ------------------------------------------------------------------

    @staticmethod
    def inline(text: str, data: bytes = None, *, url: str = None) -> 'Button':
        """Shortcut: create an inline callback or URL button."""
        if url is not None:
            return Button.url(text, url)
        return Button.inline(text, data)

    @staticmethod
    def text(label: str, **kwargs) -> 'Button':
        """Shortcut: create a reply-keyboard text button."""
        return Button.text(label, **kwargs)

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        n_rows = len(self._rows) + (1 if self._current_row else 0)
        return f'<Keyboard rows={n_rows}>'
