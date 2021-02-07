import json
import traceback
from typing import Any, List, Dict, Union, Sequence

from slack_sdk import WebClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.socket_mode import SocketModeClient

from util.util import load_json
from util.loghandler import log


class SlackWrapper:
    """
    Slack API wrapper

    Does not validate responses!
    """

    def __init__(self, slack_token, socket_mode_token, handler):
        """
        SlackWrapper constructor.
        Connect to the real-time messaging API and
        load the bot's login data.
        """
        self.client = WebClient(slack_token)

        identity = self.client.auth_test()
        identity.validate()

        self.user_id = identity["user_id"]
        self.username = identity["user"]

        self.on_message_handlers = [handler]

        self.socket = SocketModeClient(socket_mode_token)
        self.socket.connect()
        self.socket.socket_mode_request_listeners.append(self.handle)

    @property
    def connected(self):
        return self.socket.is_connected()

    def handle(self, client: SocketModeClient, message: SocketModeRequest):
        # send the response immediately so we don't get retransmissions
        client.send_socket_mode_response(SocketModeResponse(message.envelope_id))

        for handler in self.on_message_handlers:
            try:
                handler(message)
            except Exception as e:
                traceback.print_exc()
                print("error handling message", e)

    def invite_user(self, user: Union[str, Sequence[str]], channel: str) -> Dict:
        """
        Invite the given user(s) to the given channel.
        """

        return self.client.conversations_invite(channel=channel, users=user).data

    def set_purpose(self, channel: str, purpose: str) -> Dict:
        """
        Set the purpose of a given channel.
        """

        return self.client.conversations_setPurpose(channel=channel, purpose=purpose).data

    def set_topic(self, channel: str, topic: str) -> Dict:
        """Set the topic of a given channel."""

        return self.client.conversations_setTopic(channel=channel, topic=topic).data

    def get_members(self) -> List[Dict]:
        """
        Return a list of all members. Will raise exception if list fails
        """

        members = []
        for page in self.client.users_list():
            members.extend(page["members"])

        return members

    def get_member(self, user_id: str) -> Dict:
        """
        Return a member for a given user_id.
        """

        return self.client.users_info(user=user_id).data

    def create_channel(self, name: str, is_private=False) -> Dict:
        """
        Create a channel with a given name.
        """

        return self.client.conversations_create(name=name, is_private=is_private).data

    def rename_channel(self, channel_id: str, new_name: str) -> Dict:
        """
        Rename an existing channel.
        """

        return self.client.conversations_rename(channel=channel_id, name=new_name).data

    def get_channel_info(self, channel_id: str) -> Dict:
        """
        Return the channel info of a given channel ID.
        """

        return self.client.conversations_info(channel=channel_id).data

    def get_channel_members(self, channel_id: str) -> List[str]:
        """ Return list of member ids in a given channel ID. """

        members = []
        for page in self.client.conversations_members(channel=channel_id):
            members.extend(page["members"])

        return members

    def update_channel_purpose_name(self, channel_id: str, new_name: str) -> Dict:
        """
        Updates the channel purpose 'name' field for a given channel ID.
        """

        channel_info = self.get_channel_info(channel_id)

        purpose = load_json(channel_info["channel"]["purpose"]["value"])
        purpose["name"] = new_name

        return self.set_purpose(channel_id, json.dumps(purpose))

    def post_message(self, channel_id: str, text: str, timestamp="", parse="full") -> Dict:
        """
        Post a message in a given channel.
        channel_id can also be a user_id for private messages.
        Add timestamp for replying to a specific message.
        """
        if not isinstance(text, str):
            log.warning("trying to send a non-string message!")
            text = str(text)

        return self.client.chat_postMessage(channel=channel_id, text=text, as_user=True, parse=parse,
                                            thread_ts=timestamp).data

    def post_message_with_react(self, channel_id: str, text: str, reaction: str, parse="full") -> Dict:
        """Post a message in a given channel and add the specified reaction to it."""

        result = self.post_message(channel_id, text, "", parse)

        return self.client.reactions_add(channel=channel_id, name=reaction, timestamp=result["ts"]).data

    def get_message(self, channel_id: str, timestamp: str) -> Dict:
        """Retrieve a message from the channel with the specified timestamp."""

        return self.client.conversations_history(channel=channel_id, latest=timestamp, limit=1, inclusive=True).data

    def update_message(self, channel_id: str, msg_timestamp: str, text: str, parse="full") -> Dict:
        """Update a message, identified by the specified timestamp with a new text."""

        return self.client.chat_update(channel=channel_id, ts=msg_timestamp, text=text, as_user=True, parse=parse).data

    def get_channels(self, types) -> List[Dict]:
        """Paginates all channels. Will raise exception if list fails"""

        channels = []

        for page in self.client.conversations_list(types=types):
            channels.extend(page["channels"])

        return channels

    def get_public_channels(self) -> List[Dict]:
        """Fetch all public channels."""

        return self.get_channels(types="public_channel")

    def get_private_channels(self) -> List[Dict]:
        """Fetch all private channels in which the user participates."""

        return self.get_channels(types="private_channel")

    def archive_channel(self, channel_id: str) -> Dict:
        """Archive a public or private channel."""

        return self.client.conversations_archive(channel=channel_id).data

    def add_reminder_hours(self, user: str, msg: str, offset: str) -> Dict:
        """Add a reminder with a given text for the specified user."""

        return self.client.reminders_add(text=msg, time=f"in {offset} hours", user=user).data

    def get_reminders(self) -> Dict:
        """Retrieve all reminders created by the bot."""

        return self.client.reminders_list().data

    def remove_reminder(self, reminder_id: str) -> Dict:

        return self.client.reminders_delete(reminder=reminder_id).data

    def remove_reminders_by_text(self, text: str):
        """Remove all reminders that contain the specified text."""
        reminders = self.get_reminders()

        for reminder in reminders.get("reminders", []):
            if text in reminder["text"]:
                self.remove_reminder(reminder["id"])
