from telethon._impl.tl import types

from .inline_button import InlineButton


class Url(InlineButton):
    """
    Inline button that will prompt the user to open the specified URL when clicked.

    :param text: See below.
    :param url: See below.
    """

    def __init__(
        self,
        text: str,
        url: str | None = None,
        *,
        style: types.KeyboardButtonStyle,
    ) -> None:
        super().__init__(text, style=style)
        self._raw = types.KeyboardButtonUrl(
            text=text,
            url=url or text,
            style=style,
        )

    @property
    def url(self) -> str:
        """
        The URL to open.
        """
        assert isinstance(self._raw, types.KeyboardButtonUrl)
        return self._raw.url

    @url.setter
    def url(self, value: str) -> None:
        assert isinstance(self._raw, types.KeyboardButtonUrl)
        self._raw.url = value
