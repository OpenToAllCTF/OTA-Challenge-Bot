import json
import threading
import time
import websocket

from handlers.handler_factory import *
from handlers import *
from util.loghandler import *
from util.slack_wrapper import *
from bottypes.invalid_console_command import *


class BotServer(threading.Thread):

    # Global lock for locking global data in bot server
    thread_lock = threading.Lock()
    user_list = {}

    def __init__(self):
        log.debug("Parse config file and initialize threading...")
        threading.Thread.__init__(self)

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
        with open("./config.json") as f:
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
                log.info("Updated configuration: {} => {}".format(option, value))

                with open("./config.json", "w") as f:
                    json.dump(self.config, f)
            else:
                raise InvalidConsoleCommand(
                    "The specified configuration option doesn't exist: {}".format(option))
        finally:
            self.release()

    def parse_slack_message(self, message_list):
        """
        The Slack Real Time Messaging API is an events firehose.
        Return (message, channel, user) if the message is directed at the bot,
        otherwise return (None, None, None).
        """
        for msg in message_list:
            if msg.get("type") == "message" and "subtype" not in msg:
                if self.bot_at in msg.get("text", ""):
                    # Return text after the @ mention, whitespace removed
                    return msg['text'].split(self.bot_at)[1].strip().lower(), msg['channel'], msg['user']
                elif msg.get("text", "").startswith("!"):
                    # Return text after the !
                    return msg['text'][1:].strip().lower(), msg['channel'], msg['user']

        return None, None, None

    def load_bot_data(self):
        """
        Fetches the bot user information such as
        bot_name, bot_id and bot_at.
        """
        log.debug("Resolving bot user in slack")
        self.bot_name = self.slack_wrapper.username
        self.bot_id = self.slack_wrapper.user_id
        self.bot_at = "<@{}>".format(self.bot_id)
        log.debug("Found bot user {} ({})".format(self.bot_name, self.bot_id))
        self.running = True

    def run(self):
        log.info("Starting server thread...")

        self.running = True

        while self.running:
            try:
                self.load_config()
                self.slack_wrapper = SlackWrapper(
                    self.get_config_option("api_key"))

                if self.slack_wrapper.connected:
                    log.info("Connection successful...")
                    self.load_bot_data()
                    READ_WEBSOCKET_DELAY = 1  # 1 second delay between reading from firehose

                    # Might even pass the bot server for handlers?
                    log.info("Initializing handlers...")
                    HandlerFactory.initialize(
                        self.slack_wrapper, self.bot_id, self)

                    # Main loop
                    log.info("Bot is running...")
                    while self.running:
                        message = self.slack_wrapper.read()
                        command, channel, user = self.parse_slack_message(
                            message)

                        if command:
                            log.debug("Received bot command : {} ({})".format(
                                command, channel))
                            HandlerFactory.process(self.slack_wrapper, self,
                                                   command, channel, user)

                        time.sleep(READ_WEBSOCKET_DELAY)
                else:
                    log.error(
                        "Connection failed. Invalid slack token or bot id?")
                    self.running = False
            except websocket._exceptions.WebSocketConnectionClosedException:
                log.exception("Web socket error. Executing reconnect...")

        log.info("Shutdown complete...")
