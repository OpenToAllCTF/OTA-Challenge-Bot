import shlex
from unidecode import unidecode
from util.loghandler import *
from bottypes.invalid_command import *


class HandlerFactory():
    """
    Every handler should initialize the `commands` dictionary with the commands
    he can handle and the corresponding command class

    The handler factory will then check, if the handler can process a command, resolve it and execute it
    """
    handlers = {}

    def register(handler_name, handler):
        log.info("Registering new handler: %s (%s)" %
                 (handler_name, handler.__class__.__name__))

        HandlerFactory.handlers[handler_name] = handler
        handler.handler_name = handler_name

    def initialize(slack_client, bot_id):
        """
        Initializes all handler with common information.

        Might remove bot_id from here later on?
        """
        for handler in HandlerFactory.handlers:
            HandlerFactory.handlers[handler].init(slack_client, bot_id)

    def process(slack_client, botserver, msg, channel, user):
        log.debug("Processing message: %s from %s (%s)" % (msg, channel, user))

        try:
            command_line = unidecode(msg.lower())
            args = shlex.split(command_line)
        except:
            message = "Command failed : Malformed input."
            slack_client.api_call("chat.postMessage",
                                  channel=channel, text=message, as_user=True)
            return

        try:
            handler_name = args[0]

            processed = False

            usage_msg = ""

            # Call a specific handler with this command
            handler = HandlerFactory.handlers.get(handler_name)
            if handler:
                if (len(args) < 2) or (args[1] == "help"):
                    # Generic help handling
                    usage_msg += handler.usage
                    processed = True
                else:
                    command = args[1]

                    if handler.can_handle(command):
                        handler.process(slack_client, command,
                                        args[2:], channel, user)
                        processed = True
            else:
                # Pass the command to every available handler
                command = args[0]

                for handler_name in HandlerFactory.handlers:
                    handler = HandlerFactory.handlers[handler_name]

                    if command == "help":
                        usage_msg += handler.usage
                        processed = True
                    elif handler.can_handle(command):
                        handler.process(slack_client, command,
                                        args[1:], channel, user)
                        processed = True

            if not processed:
                msg = "Unknown handler or command : `%s`" % msg
                slack_client.api_call("chat.postMessage",
                                      channel=channel, text=msg, as_user=True)

            if usage_msg:
                slack_client.api_call("chat.postMessage",
                                      channel=user if botserver.get_config_option("send_help_as_dm")=="1" else channel, text=usage_msg, as_user=True)

        except InvalidCommand as e:
            slack_client.api_call(
                "chat.postMessage", channel=channel, text=e.message, as_user=True)
        except Exception as ex:
            log.exception("An error has occured while processing a command")
