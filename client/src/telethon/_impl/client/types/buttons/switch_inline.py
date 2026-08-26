from ....tl import types
from .inline_button import InlineButton


class SwitchInline(InlineButton):
    """
    Inline button that will switch the user to inline mode to trigger :class:`telethon.events.InlineQuery`.

    :param text: See below.
    :param query: See below.
    """

    def __init__(
        self,
        text: str,
        query: str | None = None,
        *,
        style: types.KeyboardButtonStyle,
    ) -> None:
        super().__init__(text, style=style)
        self._raw = types.KeyboardButtonSwitchInline(
            same_peer=False,
            text=text,
            query=query or "",
            peer_types=None,
            style=style,
        )

    @property
    def query(self) -> str:
        """
        The query string to set by default on the user's message input.
        """
        assert isinstance(self._raw, types.KeyboardButtonSwitchInline)
        return self._raw.query

    @query.setter
    def query(self, value: str) -> None:
        assert isinstance(self._raw, types.KeyboardButtonSwitchInline)
        self._raw.query = value
