import json
import threading
import time

import websocket
from slack_sdk.socket_mode.request import SocketModeRequest
from slackclient.server import SlackConnectionError

from bottypes.invalid_console_command import InvalidConsoleCommand
from handlers import *
from handlers import handler_factory
from util.loghandler import log
from util.slack_wrapper import SlackWrapper
from util.util import get_display_name, resolve_user_by_user_id


class BotServer(threading.Thread):

    # Global lock for locking global data in bot server
    thread_lock = threading.Lock()
    user_list = {}

    def __init__(self):
        log.debug("Parse config file and initialize threading...")
        threading.Thread.__init__(self)
        self.running = False
        self.config = {}
        self.bot_name = ""
        self.bot_id = ""
        self.bot_at = ""
        self.slack_wrapper = None
        self.read_websocket_delay = 1

    def lock(self):
        """Acquire global lock for working with global (not thread-safe) data."""
        BotServer.thread_lock.acquire()

    def release(self):
        """Release global lock after accessing global (not thread-safe) data."""
        BotServer.thread_lock.release()

    def quit(self):
        """Inform the application that it is quitting."""
        log.info("Shutting down")
        self.running = False

    def load_config(self):
        """Load configuration file."""
        self.lock()
        with open("./config/config.json") as f:
            self.config = json.load(f)
        self.release()

    def get_config_option(self, option):
        """Get configuration option."""
        self.lock()
        result = self.config.get(option)
        self.release()

        return result

    def set_config_option(self, option, value):
        """Set configuration option."""
        self.lock()

        try:
            if option in self.config:
                self.config[option] = value
                log.info("Updated configuration: %s => %s", option, value)

                with open("./config/config.json", "w") as f:
                    json.dump(self.config, f, indent=4)
            else:
                raise InvalidConsoleCommand("The specified configuration option doesn't exist: {}".format(option))
        finally:
            self.release()

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
                    return msg["text"].split(self.bot_at)[1].strip(), msg["channel"], msg["thread_ts"] if "thread_ts" in msg else msg["ts"], msg["user"]
                elif msg.get("text", "").startswith("!"):
                    # Return text after the !
                    return msg["text"][1:].strip(), msg["channel"], msg["thread_ts"] if "thread_ts" in msg else msg["ts"], msg["user"]
            # Check if user tampers with channel purpose
            elif msg.get("type") == "message" and msg["subtype"] == "channel_purpose" and msg["user"] != self.bot_id:
                source_user = get_display_name(resolve_user_by_user_id(self.slack_wrapper, msg["user"]))
                warning = "*User "{}" changed the channel purpose ```{}```*".format(source_user, msg["text"])
                self.slack_wrapper.post_message(msg["channel"], warning)
            # Check for deletion of messages containing keywords
            elif "subtype" in msg and msg["subtype"] == "message_deleted":
                delete_keywords = self.get_config_option("delete_watch_keywords")

                previous_msg = msg["previous_message"]["text"]

                if any(keyword in previous_msg for keyword in delete_keywords):
                    user_name = self.slack_wrapper.get_member(msg["previous_message"]["user"])
                    display_name = get_display_name(user_name)
                    self.slack_wrapper.post_message(msg["channel"], "*{}* deleted : `{}`".format(display_name, previous_msg))
            # Greet new users
            elif msg.get("type") == "im_created":
                self.slack_wrapper.post_message(msg["user"], self.get_config_option("intro_message"))

        return None, None, None, None

    def parse_slack_reaction(self, message_list):
        for msg in message_list:
            msgtype = msg.get("type")

            if msgtype in("reaction_removed", "reaction_added"):
                # Ignore reactions from the bot itself
                if msg["user"] == self.bot_id:
                    continue

                if msg["item"]:
                    return msg["reaction"], msg["item"]["channel"], msg["item"]["ts"], msg["user"]

        return None, None, None, None

    def init_bot_data(self):
        """
        Fetches the bot user information such as
        bot_name, bot_id and bot_at.
        """
        log.debug("Resolving bot user in slack")
        self.bot_name = self.slack_wrapper.username
        self.bot_id = self.slack_wrapper.user_id
        self.bot_at = "<@{}>".format(self.bot_id)
        log.debug("Found bot user %s (%s)", self.bot_name, self.bot_id)
        self.running = True

        # Might even pass the bot server for handlers?
        log.info("Initializing handlers...")
        handler_factory.initialize(self.slack_wrapper, self)

    def handle_message(self, message: SocketModeRequest):
        if message.payload["type"] != "event_callback":
            log.warning("unexpected payload type %s", message.payload["type"])
            return

        message_list = [message.payload["event"]]

        reaction, channel, time_stamp, reaction_user = self.parse_slack_reaction(message_list)

        if reaction and not self.bot_id == reaction_user:
            log.debug("Received reaction : %s (%s)", reaction, channel)
            handler_factory.process_reaction(self.slack_wrapper, reaction, time_stamp, channel, reaction_user)

        command, channel, time_stamp, user = self.parse_slack_message(message_list)

        if command and not self.bot_id == user:
            log.debug("Received bot command : %s (%s)", command, channel)
            handler_factory.process(self.slack_wrapper, self, command, time_stamp, channel, user)

    def run(self):
        log.info("Starting server thread...")

        self.running = True

        while self.running:
            try:
                self.load_config()
                self.slack_wrapper = SlackWrapper(
                    self.get_config_option("api_key"),
                    self.get_config_option("app_key"),
                    self.handle_message,
                )

                if self.slack_wrapper.connected:
                    log.info("Connection successful...")
                    self.init_bot_data()

                    # Main loop
                    log.info("Bot is running...")
                    threading.Event().wait()
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

        log.info("Shutdown complete...")
