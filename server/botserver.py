import json
import threading
import time

from slackclient import SlackClient

from handlers.handler_factory import *
from handlers import *
from util.loghandler import *


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

    def parseSlackMessage(self, slackMessage):
        """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
        """
        output_list = slackMessage

        if output_list:
            for output in output_list:
                if output and 'text' in output:
                    if self.botAT in output['text']:
                        # return text after the @ mention, whitespace removed
                        return (output['text'].split(self.botAT)[1].strip().lower(), output['channel'], output['user'])
                    elif output['text'] and output['text'].startswith('!'):
                        return (output['text'][1:].strip().lower(), output['channel'], output['user'])

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

        with open("./config.json") as f:
            config = json.load(f)

        self.slack_client = SlackClient(config['api_key'])

        self.searchBotUser(config['bot_name'])

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

                    if command and channel:
                        log.debug("Received bot command : %s (%s)" %
                                  (command, channel))

                        HandlerFactory.process(
                            self.slack_client, command, channel, user)

                    time.sleep(READ_WEBSOCKET_DELAY)
            else:
                log.error("Connection failed. Invalid slack token or bot id?")

        log.info("Shutdown complete...")
