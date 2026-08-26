from telethon._impl.tl import types

from .button import Button


class RequestPoll(Button):
    """
    Keyboard button that will prompt the user to create a poll.

    :param text: See below.
    """

    def __init__(
        self,
        text: str,
        *,
        quiz: bool = False,
        style: types.KeyboardButtonStyle,
    ) -> None:
        super().__init__(text, style=style)
        self._raw = types.KeyboardButtonRequestPoll(
            text=text,
            quiz=quiz,
            style=style,
        )
