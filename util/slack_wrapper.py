import json

import slack
from util.util import load_json

from slack.web.base_client import SlackResponse
import slack.errors as e

def handle_slack_api_error(func):
    def func_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except e.SlackApiError as ex:
            return ex.response
    return func_wrapper


class SlackWrapper:
    """
    Slack API wrapper
    """

    def __init__(self, webclient):
        self.client = webclient
        self.server = None
        self.username = None
        self.user_id = None

    @handle_slack_api_error
    def invite_user(self, user, channel, is_private=False):
        """
        Invite a user to a given channel.
        """

        api_call = "groups.invite" if is_private else "channels.invite"
        return self.client.api_call(api_call, params={"channel": channel, "user": user}).data

    @handle_slack_api_error
    def set_purpose(self, channel, purpose, is_private=False):
        """
        Set the purpose of a given channel.
        """

        api_call = "groups.setPurpose" if is_private else "channels.setPurpose"
        return self.client.api_call(api_call, params={"purpose": purpose, "channel": channel}).data

    @handle_slack_api_error
    def set_topic(self, channel, topic, is_private=False):
        """Set the topic of a given channel."""

        api_call = "groups.setTopic" if is_private else "channels.setTopic"
        return self.client.api_call(api_call, params={"topic": topic, "channel": channel}).data

    @handle_slack_api_error
    def get_members(self):
        """
        Return a list of all members.
        """
        return self.client.api_call("users.list", params={"presence": "true"}).data

    @handle_slack_api_error
    def get_member(self, user_id):
        """
        Return a member for a given user_id.
        """
        return self.client.api_call("users.info", params={"user": user_id}).data

    @handle_slack_api_error
    def create_channel(self, name, is_private=False) -> SlackResponse:
        """
        Create a channel with a given name.
        """
        api_call = "groups.create" if is_private else "channels.create"

        return self.client.api_call(api_call, params={"name": name, "validate": "false"}).data

    @handle_slack_api_error
    def rename_channel(self, channel_id, new_name, is_private=False):
        """
        Rename an existing channel.
        """
        api_call = "groups.rename" if is_private else "channels.rename"

        return self.client.api_call(api_call, params={"channel": channel_id, "name": new_name, "validate": "false"}).data

    @handle_slack_api_error
    def get_channel_info(self, channel_id, is_private=False):
        """
        Return the channel info of a given channel ID.
        """

        api_call = "groups.info" if is_private else "channels.info"
        return self.client.api_call(api_call, params={"channel": channel_id}).data

    @handle_slack_api_error
    def get_channel_members(self, channel_id, is_private=False):
        """ Return list of member ids in a given channel ID. """

        return self.get_channel_info(channel_id, is_private).data['channel']['members']
    
    def update_channel_purpose_name(self, channel_id, new_name, is_private=False):
        """
        Updates the channel purpose 'name' field for a given channel ID.
        """

        # Update channel purpose
        channel_info = self.get_channel_info(channel_id, is_private)
        key = "group" if is_private else "channel"

        if channel_info:
            purpose = load_json(channel_info[key]['purpose']['value'])
            purpose['name'] = new_name

            self.set_purpose(channel_id, json.dumps(purpose), is_private)

    def post_message(self, channel_id, text, timestamp="", parse="full"):
        """
        Post a message in a given channel.
        channel_id can also be a user_id for private messages.
        Add timestamp for replying to a specific message.
        """
        self.client.api_call("chat.postMessage", params={"channel":channel_id, "text":text, "as_user":"true", "parse":parse if parse else "none", "thread_ts":timestamp})

    def post_message_with_react(self, channel_id, text, reaction, parse="full"):
        """Post a message in a given channel and add the specified reaction to it."""
        result = self.client.api_call("chat.postMessage", params={
                                      "channel": channel_id, "text": text, "as_user": "true", "parse": parse}).data

        if result["ok"]:
            self.client.api_call("reactions.add", params={
                                 "channel": channel_id, "name": reaction, "timestamp": result["ts"]})

    @handle_slack_api_error
    def get_message(self, channel_id, timestamp):
        """Retrieve a message from the channel with the specified timestamp."""
        return self.client.api_call("channels.history", params={"channel": channel_id, "latest": timestamp, "count": 1, "inclusive": "true"}).data

    def update_message(self, channel_id, msg_timestamp, text, parse="full"):
        """Update a message, identified by the specified timestamp with a new text."""
        self.client.api_call("chat.update", params={
                             "channel": channel_id, "text": text, "ts": msg_timestamp, "as_user": "true", "parse": parse})

    @handle_slack_api_error
    def get_public_channels(self):
        """Fetch all public channels."""
        return self.client.api_call("channels.list", params={"exclude_archived":"true"}).data

    @handle_slack_api_error
    def get_private_channels(self):
        """Fetch all private channels in which the user participates."""
        return self.client.api_call("groups.list", params={"exclude_archived":"true"}).data

    @handle_slack_api_error
    def archive_private_channel(self, channel_id):
        """Archive a private channel"""
        return self.client.api_call("groups.archive", params={"channel": channel_id}).data

    @handle_slack_api_error
    def archive_public_channel(self, channel_id):
        """Archive a public channel"""
        return self.client.api_call("channels.archive", params={"channel": channel_id}).data
