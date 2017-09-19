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
    """Ping this server to check for uptime."""

    def execute(self, slack_wrapper, args, channel_id, user_id):
        """Announce the bot's presence in the channel."""
        slack_wrapper.post_message(channel_id, "Pong!")

class BotHandler(BaseHandler):
    """Ping this server to check for uptime."""
    def __init__(self):
        self.commands = {
            "ping": CommandDesc(PingCommand, "Ping the bot", None, None)
        }

HandlerFactory.register("bot", BotHandler())
