import json
import threading
import time

import websocket
import slack

from bottypes.invalid_console_command import InvalidConsoleCommand
from handlers import *
from handlers import handler_factory
from util.loghandler import log
from util.slack_wrapper import SlackWrapper
from util.util import get_display_name, resolve_user_by_user_id

bot = None


class BotServer():
    def __init__(self):
        # TODO: Remove the need of global bot...
        global bot

        self.config = {}
        self.bot_name = ""
        self.bot_id = ""
        self.bot_at = ""

        bot = self

    def load_config(self):
        with open("./config.json") as f:
            self.config = json.load(f)

    def get_config_option(self, option):
        result = self.config.get(option)
        return result

    def set_config_option(self, option, value):
        if option in self.config:
            self.config[option] = value
            log.info("Updated configuration: %s => %s", option, value)
            with open("./config.json", "w") as f:
                json.dump(self.config, f)
        else:
            raise InvalidConsoleCommand(
                "The specified configuration option doesn't exist: {}".format(option))

    def init_bot_data(self, slack_wrapper, name, id):
        log.debug("Resolving bot user in slack")
        self.bot_name = name
        self.bot_id = id
        self.bot_at = "<@{}>".format(self.bot_id)

        log.debug("Found bot user %s (%s)", self.bot_name, self.bot_id)

        # Might even pass the bot server for handlers?
        log.info("Initializing handlers...")        
        handler_factory.initialize(slack_wrapper, self)

    def parse_slack_message(self, msg, slack_wrapper):
        if self.bot_at in msg.get("text", ""):
            pass
        elif msg.get("text", "").startswith("!"):
            return msg['text'][1:].strip(), msg['channel'], msg['thread_ts'] if 'thread_ts' in msg else msg['ts'], msg['user']
        elif msg.get("subtype", "") == "channel_purpose" and msg["user"] != self.bot_id:
            # Check if user tampers with channel purpose            
            source_user = get_display_name(resolve_user_by_user_id(slack_wrapper, msg['user']))
            warning = "*User '{}' changed the channel purpose ```{}```*".format(source_user, msg['text'])
            slack_wrapper.post_message(msg['channel'], warning)

        return None, None, None, None

    def parse_slack_reaction(self, msg):
        # Ignore reactions from the bot it
        if msg["item"] and not msg["user"] == self.bot_id:
            return msg["reaction"], msg["item"]["channel"], msg["item"]["ts"], msg["user"]

        return None, None, None, None

    def handle_reaction(self, message, webclient):
        reaction, channel, time_stamp, reaction_user = self.parse_slack_reaction(
            message)

        if reaction:
            log.debug("Received reaction : %s (%s)", reaction, channel)
            wrapper = SlackWrapper(webclient)
            handler_factory.process_reaction(
                wrapper, reaction, time_stamp, channel, reaction_user)

    def handle_message(self, message, slack_wrapper):        
        command, channel, time_stamp, user = self.parse_slack_message(message, slack_wrapper)

        if command:
            log.debug("Received bot command : %s (%s)", command, channel)            
            handler_factory.process(slack_wrapper, self, command, time_stamp, channel, user)

    def start_bot(self):
        log.info("Starting bot rtm client...")
        self.load_config()
        slack_token = self.get_config_option("api_key")
        rtmclient = slack.RTMClient(token=slack_token)
        rtmclient.start()


@slack.RTMClient.run_on(event='open')
def handle_slack_open(**payload):
    # TODO: can those events be moved into the botserver?
    global bot
    data = payload["data"]
    bot.init_bot_data(SlackWrapper(payload["web_client"]), data['self']['name'], data['self']['id'] )


@slack.RTMClient.run_on(event='message')
def handle_slack_message(**payload):
    # TODO: can those events be moved into the botserver?
    global bot
    message = payload['data']

    try:
        if message:
            slack_wrapper = SlackWrapper(payload["web_client"])
            bot.handle_message(message, slack_wrapper)
    except Exception as ex:
        log.error("Exception on parsing: %s" % ex)


def handle_slack_reaction(payload):
    # TODO: can this be moved back into botserver?
    global bot

    try:
        if payload["data"]:
            bot.handle_reaction(payload["data"], payload["web_client"])
    except Exception as ex:
        log.error("Exception on parsing reaction: %s" % ex)


@slack.RTMClient.run_on(event='reaction_added')
def handle_slack_reaction_added(**payload):
    handle_slack_reaction(payload)


@slack.RTMClient.run_on(event='reaction_removed')
def handle_slack_reaction_removed(**payload):
    handle_slack_reaction(payload)
