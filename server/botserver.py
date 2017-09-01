import json
import threading
import time

from slackclient import SlackClient

from handlers.handler_factory import *
from handlers import *
from util.loghandler import *
from bottypes.invalid_console_command import *

class BotServer(threading.Thread):

    # global lock for locking global data in bot server
    threadLock = threading.Lock()
    userList = []

    def __init__(self):
        log.debug("Parse config file and initialize threading...")

        threading.Thread.__init__(self)

    def lock(self):
        """Acquire global lock for working with global (not thread-safe) data."""
        BotServer.threadLock.acquire()

    def release(self):
        """Release global lock after accessing global (not thread-safe) data."""
        BotServer.threadLock.release()

    def updateUserList(self, slack_client):
        self.lock()

        log.debug("Retrieving user list")

        api_call = slack_client.api_call("users.list")
        if api_call.get('ok'):
            BotServer.userList = api_call.get('members')

        self.release()

    def getUser(self, userName):
        self.lock()

        foundUser = None

        for user in BotServer.userList:
            if 'name' in user and user.get('name') == userName:
                foundUser = user
                break

        self.release()

        return foundUser

    def quit(self):
        log.info("Shutting down")

        self.running = False

    def sendMessage(self, channelID, msg):
        self.slack_client.api_call(
            "chat.PostMessage", channel=channelID, text=msg, as_user=True)

    def load_config(self):
        self.lock()

        with open("./config.json") as f:
            self.config = json.load(f)

        self.release()

    def get_config_option(self, option):
        self.lock()

        result = None

        if option in self.config:
            result = self.config[option]

        self.release()

        return result

    def set_config_option(self, option, value):
        self.lock()

        try:
            if option in self.config:
                self.config[option] = value

                log.info("Updated configuration: {} => {}".format(option, value))

                with open("./config.json", "w") as f:
                    json.dump(self.config, f)
            else:
                raise InvalidConsoleCommand("The specified configuration option doesn't exist: {}".format(option))
        finally:
            self.release()

    def parseSlackMessage(self, slackMessage):
        """
        The Slack Real Time Messaging API is an events firehose.
        Return (message, channel, user) if the message is directed at the bot,
        otherwise return (None, None, None).
        """
        message_list = slackMessage

        for msg in message_list:
            if msg.get("type") == "message":
                if self.botAT in msg.get("text", ""):
                    # return text after the @ mention, whitespace removed
                    return msg['text'].split(self.botAT)[1].strip().lower(), msg['channel'], msg['user']
                elif msg.get("text", "").startswith('!'):
                    # return text after the !
                    return msg['text'][1:].strip().lower(), msg['channel'], msg['user']

        return None, None, None

    def searchBotUser(self, botName):
        log.debug("Trying to resolve bot user in slack")

        self.updateUserList(self.slack_client)

        self.botName = botName
        botUser = self.getUser(self.botName)

        if botUser:
            self.botID = botUser['id']
            self.botAT = "<@%s>" % self.botID

            log.debug("Found bot user %s (%s)" % (self.botName, self.botID))

            self.running = True
        else:
            log.error("Could not find bot user. Abort...")

            self.running = False

    def run(self):
        log.info("Starting server thread...")

        self.load_config()

        self.slack_client = SlackClient(self.get_config_option('api_key'))

        self.searchBotUser(self.get_config_option('bot_name'))

        if self.botID:
            # 1 second delay between reading from firehose
            READ_WEBSOCKET_DELAY = 1

            if self.slack_client.rtm_connect():
                log.info("Connection successful...")

                log.info("Initializing handlers...")
                # Might even pass the bot server for handlers?
                HandlerFactory.initialize(
                    self.slack_client, self.botID)

                # Main loop
                while self.running:
                    command, channel, user = self.parseSlackMessage(
                        self.slack_client.rtm_read())

                    if command:
                        log.debug("Received bot command : %s (%s)" %
                                  (command, channel))

                        HandlerFactory.process(
                            self.slack_client, self, command, channel, user)

                    time.sleep(READ_WEBSOCKET_DELAY)
            else:
                log.error("Connection failed. Invalid slack token or bot id?")

        log.info("Shutdown complete...")
