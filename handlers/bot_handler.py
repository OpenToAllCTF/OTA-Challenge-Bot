import shlex
import pickle
import re
import json

from unidecode import unidecode

from bottypes.command import *
from bottypes.command_descriptor import *
from handlers.handler_factory import *
from handlers.base_handler import *


class PingCommand(Command):
    """
    Ping this server to check for uptime.
    """
    def execute(self, slack_client, args, channel, user):
        # Announce the CTF channel
        message = "Pong!"

        slack_client.api_call("chat.postMessage", channel=channel, text=message, as_user=True)


class BotHandler(BaseHandler):
    """
    Ping this server to check for uptime.
    """
    def __init__(self):
        self.commands = {
                "ping" : CommandDesc(PingCommand, "Ping the bot", None, None)
        }

HandlerFactory.registerHandler("bot", BotHandler())
