import shlex
import pickle
import re
import json

from unidecode import unidecode

from bottypes.command import *
from bottypes.command_descriptor import *
import handlers.handler_factory as handler_factory
from handlers.base_handler import *
from util.githandler import GitHandler
from util.loghandler import log


class PingCommand(Command):
    """Ping this server to check for uptime."""

    def execute(self, slack_wrapper, args, channel_id, user_id):
        """Announce the bot's presence in the channel."""
        slack_wrapper.post_message(channel_id, "Pong!")


class IntroCommand(Command):
    """Show an introduction message for new members."""

    def execute(self, slack_wrapper, args, channel_id, user_id):
        """Execute the Intro command."""
        try:
            with open("intro_msg") as f:
                message = f.read()

            slack_wrapper.post_message(channel_id, message)
        except:
            message = "Sorry, I forgot what I wanted to say (or the admins forgot to give me an intro message :wink:)"

            slack_wrapper.post_message(channel_id, message)


class VersionCommand(Command):
    """Show git information about the current running version of the bot."""

    def execute(self, slack_wrapper, args, channel_id, user_id):
        """Execute the Version command."""
        try:
            message = GitHandler(".").get_version()

            slack_wrapper.post_message(channel_id, message)
        except:
            log.exception("BotHandler::VersionCommand")
            raise InvalidCommand("Sorry, couldn't retrieve the git information for the bot...")


class BotHandler(BaseHandler):
    """Handler for generic bot commands."""

    def __init__(self):
        self.commands = {
            "ping": CommandDesc(PingCommand, "Ping the bot", None, None),
            "intro": CommandDesc(IntroCommand, "Show an introduction message for new members", None, None),
            "version": CommandDesc(VersionCommand, "Show git information about the running version of the bot", None, None)
        }


handler_factory.register("bot", BotHandler())
