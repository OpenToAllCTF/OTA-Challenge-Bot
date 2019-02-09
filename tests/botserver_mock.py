import json
import threading
import time
import websocket

import handlers.handler_factory as handler_factory
from handlers import *
from util.loghandler import *
from tests.slackwrapper_mock import SlackWrapperMock
from bottypes.invalid_console_command import *
from slackclient.server import SlackConnectionError


class BotServerMock():
    user_list = {}

    def __init__(self):
        log.debug("Parse config file and initialize threading...")
        self.running = False
        self.config = {}
        self.bot_name = "unittest_bot"
        self.bot_id = "unittest_botid"
        self.bot_at = "@unittest_bot"
        self.slack_wrapper = SlackWrapperMock("unittest_apikey")

    def quit(self):
        """Inform the application that it is quitting."""
        self.running = False

    def load_config(self):
        """Load configuration file."""
        self.config = {
            "bot_name": "unittest_bot",
            "api_key": "unittest_apikey",
            "send_help_as_dm": "1",
            "admin_users": [
                "admin_user"
            ],
            "auto_invite": [],
            "wolfram_app_id": "wolfram_dummyapi"
        }

    def get_config_option(self, option):
        """Get configuration option."""
        result = self.config.get(option)

        return result

    def set_config_option(self, option, value):
        """Set configuration option."""

        if option in self.config:
            self.config[option] = value
            log.info("Updated configuration: {} => {}".format(option, value))
        else:
            raise InvalidConsoleCommand("The specified configuration option doesn't exist: {}".format(option))

    def parse_slack_message(self, message_list):
        """
        The Slack Real Time Messaging API is an events firehose.
        Return (message, channel, ts, user) if the message is directed at the bot,
        otherwise return (None, None, None, None).
        """
        for msg in message_list:
            if msg.get("type") == "message" and "subtype" not in msg:
                if self.bot_at in msg.get("text", ""):
                    # Return text after the @ mention, whitespace removed
                    return msg['text'].split(self.bot_at)[1].strip(), msg['channel'], msg['thread_ts'] if 'thread_ts' in msg else msg['ts'], msg['user']
                elif msg.get("text", "").startswith("!"):
                    # Return text after the !
                    return msg['text'][1:].strip(), msg['channel'], msg['thread_ts'] if 'thread_ts' in msg else msg['ts'], msg['user']

        return None, None, None, None

    def parse_slack_reaction(self, message_list):
        for msg in message_list:
            msgtype = msg.get("type")

            if msgtype == "reaction_removed" or msgtype == "reaction_added":
                # Ignore reactions from the bot itself
                if msg["user"] == self.bot_id:
                    continue

                if msg["item"]:
                    return msg["reaction"], msg["item"]["channel"], msg["item"]["ts"], msg["user"]

        return None, None, None, None

    def load_bot_data(self):
        """
        Fetches the bot user information such as
        bot_name, bot_id and bot_at.
        """
        self.bot_name = self.slack_wrapper.username
        self.bot_id = self.slack_wrapper.user_id
        self.bot_at = "<@{}>".format(self.bot_id)
        self.running = True

    def test_command(self, msg, exec_user="normal_user"):
        """Run the command as the specified user in the test environment."""
        testmsg = [{'type': 'message', 'user': exec_user, 'text': msg, 'client_msg_id': '738e4beb-d50e-42a4-a60e-3fafd4bd71da',
                    'team': 'UNITTESTTEAMID', 'channel': 'UNITTESTCHANNELID', 'event_ts': '1549715670.002000', 'ts': '1549715670.002000'}]
        self.exec_message(testmsg)

    def test_reaction(self, reaction, exec_user="normal_user"):
        """Run the specified reaction as the specified user in the test environment."""
        testmsg = [{'type': 'reaction_added', 'user': exec_user, 'item': {'type': 'message', 'channel': 'UNITTESTCHANNELID', 'ts': '1549117537.000500'},
                    'reaction': reaction, 'item_user': 'UNITTESTUSERID', 'event_ts': '1549715822.000800', 'ts': '1549715822.000800'}]

        self.exec_message(testmsg)

    def check_for_response_available(self):
        return len(self.slack_wrapper.message_list) > 0

    def check_for_response(self, expected_result):
        """ Check if the simulated slack responses contain an expected result. """
        for msg in self.slack_wrapper.message_list:
            if expected_result in msg.message:
                return True

        return False

    def exec_message(self, testmsg):
        self.running = True

        while self.running:
            try:
                self.load_config()
                self.slack_wrapper = SlackWrapperMock("testapikey")

                if self.slack_wrapper.connected:
                    self.load_bot_data()
                    READ_WEBSOCKET_DELAY = 1  # 1 second delay between reading from firehose

                    # Might even pass the bot server for handlers?
                    handler_factory.initialize(self.slack_wrapper, self.bot_id, self)

                    # Main loop
                    while self.running:
                        message = testmsg
                        if message:
                            reaction, channel, ts, reaction_user = self.parse_slack_reaction(message)

                            if reaction:
                                log.debug("Received reaction : {} ({})".format(reaction, channel))
                                handler_factory.process_reaction(
                                    self.slack_wrapper, reaction, ts, channel, reaction_user)

                            command, channel, ts, user = self.parse_slack_message(message)

                            if command:
                                log.debug("Received bot command : {} ({})".format(command, channel))
                                handler_factory.process(self.slack_wrapper, self,
                                                        command, ts, channel, user)

                            # We're in test context, immediately stop
                            self.running = False
                else:
                    log.error("Connection failed. Invalid slack token or bot id?")
                    self.running = False
            except websocket._exceptions.WebSocketConnectionClosedException:
                log.exception("Web socket error. Executing reconnect...")
            except SlackConnectionError:
                # Try to reconnect if slackclient auto_reconnect didn't work out. Keep an eye on the logfiles,
                # and remove the superfluous exception handling if auto_reconnect works.
                log.exception("Slack connection error. Trying manual reconnect in 5 seconds...")
                time.sleep(5)
            except:
                log.exception("Unhandled error. Try reconnect...")
                time.sleep(5)
