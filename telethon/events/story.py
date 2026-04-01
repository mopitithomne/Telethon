from .common import EventBuilder, EventCommon, name_inner_event, _into_id_set
from .. import utils
from ..tl import types


@name_inner_event
class Story(EventBuilder):
    """
    Occurs whenever a story is posted, updated, or expires.

    Args:
        added (`bool`, optional):
            If `True`, only newly posted stories trigger this event.
            Mutually exclusive with ``deleted``.

        deleted (`bool`, optional):
            If `True`, only story deletions trigger this event.
            Mutually exclusive with ``added``.

        from_users (`entity`, optional):
            Only stories posted *by* these users will be handled.

    Example
        .. code-block:: python

            from telethon import TelegramClient, events

            # Any story activity
            @client.on(events.Story)
            async def handler(event):
                print(f'Story update from {event.sender_id}: {event}')

            # Only freshly posted stories
            @client.on(events.Story(added=True))
            async def on_new_story(event):
                print(f'New story from {event.sender_id}')

            # Only story deletions from a specific user
            @client.on(events.Story(deleted=True, from_users='some_user'))
            async def on_story_deleted(event):
                print('Story removed')
    """

    def __init__(self, chats=None, *, blacklist_chats=False, func=None,
                 added=None, deleted=None, from_users=None):
        if added and deleted:
            raise ValueError("'added' and 'deleted' are mutually exclusive")
        super().__init__(chats, blacklist_chats=blacklist_chats, func=func)
        self.added = added
        self.deleted = deleted
        self.from_users = from_users

    async def _resolve(self, client):
        await super()._resolve(client)
        self.from_users = await _into_id_set(client, self.from_users)

    @classmethod
    def build(cls, update, others=None, self_id=None):
        if isinstance(update, types.UpdateStory):
            return cls.Event(update, deleted=False)
        if isinstance(update, types.UpdateStoriesStealthMode):
            # Stealth-mode toggle — not really a story event, skip unless
            # the user explicitly registers a Raw handler.
            return None
        return None

    def filter(self, event):
        if not (result := super().filter(event)):
            return result

        if self.added is True and event.deleted:
            return None
        if self.deleted is True and not event.deleted:
            return None

        if self.from_users is not None:
            if event.sender_id not in self.from_users:
                return None

        if self.func:
            return self.func(event)
        return event

    class Event(EventCommon):
        """
        Represents a story update event.

        Members:
            update (:tl:`UpdateStory`):
                The raw Telegram update.

            deleted (`bool`):
                ``True`` when the story has been deleted (``StoryItemDeleted``).

            story (:tl:`StoryItem` | :tl:`StoryItemDeleted` | :tl:`StoryItemSkipped`):
                The story object from the update.

            story_id (`int`):
                Numeric story ID.

            sender_id (`int`):
                User/channel ID that owns the story.
        """

        def __init__(self, update, *, deleted=False):
            peer = update.peer
            super().__init__(peer)
            self.update = update
            self.story = update.story

            story = update.story
            if isinstance(story, (types.StoryItemDeleted, types.StoryItemSkipped)):
                self.story_id = story.id
                self._deleted = True
            else:
                self.story_id = story.id
                self._deleted = False

        @property
        def deleted(self):
            """``True`` if this story has been deleted."""
            return isinstance(self.story, types.StoryItemDeleted)

        @property
        def sender_id(self):
            """Integer ID of the story's owner."""
            return utils.get_peer_id(self.update.peer)

        @property
        def media(self):
            """
            The story media (photo or video), or ``None`` for deleted/skipped
            stories.
            """
            if isinstance(self.story, types.StoryItem):
                return self.story.media
            return None

        @property
        def caption(self):
            """Story caption text, or ``None``."""
            if isinstance(self.story, types.StoryItem):
                return self.story.caption
            return None

        @property
        def expire_date(self):
            """UTC datetime when the story expires, or ``None``."""
            if isinstance(self.story, types.StoryItem):
                return self.story.expire_date
            return None

        async def get_sender(self):
            """Fetches the entity that posted this story."""
            return await self._client.get_entity(self.update.peer)
