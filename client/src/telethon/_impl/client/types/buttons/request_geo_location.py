from telethon._impl.tl import types

from .button import Button


class RequestGeoLocation(Button):
    """
    Keyboard button that will prompt the user to share the geo point with their current location.

    :param text: See below.
    """

    def __init__(
        self,
        text: str,
        *,
        style: types.KeyboardButtonStyle,
    ) -> None:
        super().__init__(text, style=style)
        self._raw = types.KeyboardButtonRequestGeoLocation(text=text, style=style)
