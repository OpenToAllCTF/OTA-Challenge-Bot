import wolframalpha

from bottypes.command import Command
from bottypes.command_descriptor import CommandDesc
from handlers import handler_factory
from handlers.base_handler import BaseHandler


class AskCommand(Command):
    """Asks wolfram alpha a question and shows the answer."""

    @classmethod
    def execute(cls, slack_wrapper, args, timestamp, channel_id, user_id, user_is_admin):
        """Execute the Ask command."""
        app_id = handler_factory.botserver.get_config_option("wolfram_app_id")

        verbose = (args[0] if args else "") == "-v"

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
                                if len(subpod.plaintext) > 512:
                                    answer += "*shortened*"
                else:
                    answer = next(res.results, None)

                    if answer:
                        if len(answer.text) > 2048:
                            answer = answer.text[:2048] + "*shortened*"
                        else:
                            answer = answer.text

                slack_wrapper.post_message(channel_id, answer)
            except Exception as ex:
                if "Invalid appid" in str(ex):
                    response = "Wolfram Alpha app id doesn't seem to be correct (or api is choking)..."
                else:
                    response = "Wolfram Alpha doesn't seem to understand you :("

                slack_wrapper.post_message(channel_id, response)
        else:
            response = "It seems you have no valid wolfram alpha app id. Contact an admin about this..."

            slack_wrapper.post_message(channel_id, response)


class WolframHandler(BaseHandler):
    """
    Handles questions for wolfram alpha engine.

    Commands :
    # Ask wolfram alpha a question
    !wolfram ask
    """

    def __init__(self):
        self.commands = {
            "ask": CommandDesc(AskCommand, "Ask wolfram alpha a question (add -v for verbose answer)", ["question"], None, False),
        }


handler_factory.register("wolfram", WolframHandler())
