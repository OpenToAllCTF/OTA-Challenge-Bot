import json
from tests.slack_test_response import SlackResponse
from util.util import load_json

class SlackWrapperMock:
    """
    Slack API wrapper mock
    """

    def __init__(self, api_key):
        """
        SlackWrapper constructor.
        Connect to the real-time messaging API and
        load the bot's login data.
        """
        self.server = None
        self.username = None
        self.user_id = None

        self.connected = True

        self.message_list = []

        # create default slack responses (these responses can be swapped for more specific unit tests in the unit test itself)
        self.create_channel_private_response = self.read_test_file(
            "tests/testfiles/create_channel_private_response_default.json")
        self.create_channel_public_response = self.read_test_file(
            "tests/testfiles/create_channel_public_response_default.json")
        self.get_members_response = self.read_test_file("tests/testfiles/get_members_response_default.json")
        self.get_member_response = self.read_test_file("tests/testfiles/get_member_response_default.json")
        self.get_private_channels_response = self.read_test_file(
            "tests/testfiles/get_private_channels_response_default.json")
        self.get_public_channels_response = self.read_test_file(
            "tests/testfiles/get_public_channels_response_default.json")
        self.set_purpose_response = self.read_test_file("tests/testfiles/set_purpose_response_default.json")

    def read_test_file(self, file):
        with open(file, "r") as f:
            return f.read()

    def push_message(self, channel, msg):
        """Simulates slack post_message by storing the message in a dummy queue, which can be read from unit tests."""
        self.message_list.append(SlackResponse(msg, channel))

    def read(self):
        """Read from the real-time messaging API."""
        return "mocked response"

    def invite_user(self, user, channel, is_private=False):
        # TODO: Add test response for invite_user
        return None

    def set_purpose(self, channel, purpose, is_private=False):
        """Set the purpose of a given channel."""

        return json.loads(self.set_purpose_response.replace("PURPOSE_PH", json.dumps(purpose)))

    def get_members(self):
        return json.loads(self.get_members_response)

    def get_member(self, user_id):
        return json.loads(self.get_member_response)

    def create_channel(self, name, is_private=False):
        if is_private:
            return json.loads(self.create_channel_private_response.replace("NAME_PH", name))
        else:
            return json.loads(self.create_channel_public_response.replace("NAME_PH", name))

    def rename_channel(self, channel_id, new_name, is_private=False):
        # TODO: Add test response for rename_channel
        return None

    def get_channel_info(self, channel_id, is_private=False):
        # TODO: Add test response for get_channel_info
        return ""

    def update_channel_purpose_name(self, channel_id, new_name, is_private=False):
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
        self.push_message(channel_id, str(text))

    def post_message_with_react(self, channel_id, text, reaction, parse="full"):
        """Post a message in a given channel and add the specified reaction to it."""
        self.push_message(channel_id, text)

    def get_message(self, channel_id, timestamp):
        """Retrieve a message from the channel with the specified timestamp."""
        # TODO: Add test response for get_message
        return None

    def update_message(self, channel_id, msg_timestamp, text, parse="full"):
        """Update a message, identified by the specified timestamp with a new text."""
        # TODO: Add test response for update_message
        pass

    def get_public_channels(self):
        """Fetch all public channels."""
        return json.loads(self.get_public_channels_response)

    def get_private_channels(self):
        """Fetch all private channels in which the user participates."""
        return json.loads(self.get_private_channels_response)

    def archive_channel(self, channel_id):
        """Archive a public or private channel."""
        # TODO: The git handler must be mocked before testing archive command to avoid uploading test cases
        pass

    def set_topic(self, channel, topic, is_private=False):
        """Set the topic of a given channel."""

        return None
