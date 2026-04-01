from .common import EventBuilder, EventCommon, name_inner_event, _into_id_set
from .. import utils
from ..tl import types
from ..tl.custom.chatgetter import ChatGetter


@name_inner_event
class Reaction(EventBuilder):
    """
    Occurs whenever a message reaction is updated.

    Args:
        emoji (`str`, optional):
            If set, only reactions matching this emoji will be handled.
            For custom emoji, pass the document ID as a string.

        from_users (`entity`, optional):
            Unlike `chats`, this filters the *senders* of the reaction.
            Only reactions *sent by these users* will be handled.

    Example
        .. code-block:: python

            from telethon import TelegramClient, events

            @client.on(events.Reaction)
            async def handler(event):
                print(f'{event.sender_id} reacted with {event.emoji} on message {event.msg_id}')

            # Only handle "thumbs up" reactions in a specific chat
            @client.on(events.Reaction(chats=my_channel, emoji='👍'))
            async def handler(event):
                await client.send_message(my_channel, 'Someone liked a post!')
    """

    def __init__(self, chats=None, *, blacklist_chats=False, func=None,
                 emoji=None, from_users=None):
        super().__init__(chats, blacklist_chats=blacklist_chats, func=func)
        self.emoji = emoji
        self.from_users = from_users

    async def _resolve(self, client):
        await super()._resolve(client)
        self.from_users = await _into_id_set(client, self.from_users)

    @classmethod
    def build(cls, update, others=None, self_id=None):
        if isinstance(update, types.UpdateMessageReactions):
            return cls.Event(update)
        return None

    def filter(self, event):
        if not (result := super().filter(event)):
            return result

        if self.emoji is not None:
            if event.emoji != self.emoji:
                return None

        if self.from_users is not None:
            # UpdateMessageReactions doesn't carry a single user; it carries
            # a list of recent reactors in update.reactions.recent_reactions.
            # We match if *any* of the recent reactors is in our from_users set.
            recent = event.update.reactions.recent_reactions or []
            reactor_ids = set()
            for r in recent:
                if isinstance(r.peer_id, types.PeerUser):
                    reactor_ids.add(utils.get_peer_id(r.peer_id))
            if not reactor_ids.intersection(self.from_users):
                return None

        if self.func:
            return self.func(event)
        return event

    class Event(EventCommon):
        """
        Represents the event of a message reaction update.

        Members:
            update (:tl:`UpdateMessageReactions`):
                The original Telegram update object.

            msg_id (`int`):
                The ID of the message that was reacted to.

            emoji (`str` | `None`):
                The most recently added reaction emoji, or ``None`` if no
                new reactions were detected in recent_reactions.

            reactions (:tl:`MessageReactions`):
                The full :tl:`MessageReactions` object with counts and
                recent reactors.
        """

        def __init__(self, update):
            super().__init__(update.peer, msg_id=update.msg_id)
            self.update = update
            self.msg_id = update.msg_id
            self.reactions = update.reactions

        @property
        def emoji(self):
            """
            Returns the emoji string of the most recently added reaction, or
            ``None`` when not determinable from the update.
            """
            recent = self.update.reactions.recent_reactions or []
            if recent:
                r = recent[0].reaction
                if isinstance(r, types.ReactionEmoji):
                    return r.emoticon
                if isinstance(r, types.ReactionCustomEmoji):
                    return str(r.document_id)
            # Fall back to max-count reaction
            results = self.update.reactions.results or []
            if results:
                r = max(results, key=lambda x: x.count).reaction
                if isinstance(r, types.ReactionEmoji):
                    return r.emoticon
                if isinstance(r, types.ReactionCustomEmoji):
                    return str(r.document_id)
            return None

        @property
        def reaction_counts(self):
            """
            Returns a ``dict`` mapping emoji string → count for all current
            reactions on the message.
            """
            out = {}
            for result in (self.update.reactions.results or []):
                r = result.reaction
                if isinstance(r, types.ReactionEmoji):
                    out[r.emoticon] = result.count
                elif isinstance(r, types.ReactionCustomEmoji):
                    out[str(r.document_id)] = result.count
            return out

        async def get_message(self):
            """Fetches the :tl:`Message` this reaction belongs to."""
            return await self._client.get_messages(await self.get_input_chat(),
                                                   ids=self.msg_id)
