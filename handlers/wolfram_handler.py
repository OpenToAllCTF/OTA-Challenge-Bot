import re

import wolframalpha

from bottypes.command import *
from bottypes.command_descriptor import *
from bottypes.invalid_command import *
import handlers.handler_factory as handler_factory
from handlers.base_handler import *
from addons.syscalls.syscallinfo import *
from util.util import *


class AskCommand(Command):
    """Asks wolfram alpha a question and shows the answer."""

    @classmethod
    def execute(cls, slack_wrapper, args, channel_id, user_id, user_is_admin):
        """Execute the Ask command."""
        app_id = handler_factory.botserver.get_config_option("wolfram_app_id")

        verbose = (args[0] if len(args)>0 else "") == "-v"

        if app_id:
            try:
                if verbose:
                    question = " ".join(args[1:])
                else:
                    question = " ".join(args)

                client = wolframalpha.Client(app_id)
                res = client.query(question)

                answer = ""

                if verbose:
                    for pod in res.pods:
                        for subpod in pod.subpods:
                            if "plaintext" in subpod.keys() and subpod["plaintext"]:
                                answer += "```\n"
                                answer += subpod.plaintext[:512] + "\n"
                                answer += "```\n"
                                if (len(subpod.plaintext) > 512):
                                    answer += "*shortened*"
                else:
                    answer = next(res.results, None)

                    if answer:
                        answer = answer.text

                WolframHandler.send_message(slack_wrapper, channel_id, user_id, answer)
            except Exception as ex:
                if "Invalid appid" in str(ex):
                    response = "Wolfram Alpha app id doesn't seem to be correct (or api is choking)..."
                else:
                    response = "Wolfram Alpha doesn't seem to understand you :("

                WolframHandler.send_message(slack_wrapper, channel_id, user_id, response)
        else:
            response = "It seems you have no valid wolfram alpha app id. Contact an admin about this..."

            WolframHandler.send_message(slack_wrapper, channel_id, user_id, response)


class WolframHandler(BaseHandler):
    """
    Handles questions for wolfram alpha engine.

    Commands :
    # Ask wolfram alpha a question
    !wolfram ask
    """

    @staticmethod
    def send_message(slack_wrapper, channel_id, user_id, msg):
        """Send message to user or channel, depending on configuration."""
        slack_wrapper.post_message(channel_id, msg)

    def __init__(self):
        self.commands = {
            "ask": CommandDesc(AskCommand, "Ask wolfram alpha a question (add -v for verbose answer)", ["question"], None, False),
        }


handler_factory.register("wolfram", WolframHandler())
