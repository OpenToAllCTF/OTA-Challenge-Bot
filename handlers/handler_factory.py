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
    botserver = None

    def register(handler_name, handler):
        log.info("Registering new handler: {} ({})".format(handler_name, handler.__class__.__name__))

        HandlerFactory.handlers[handler_name] = handler
        handler.handler_name = handler_name

    def initialize(slack_wrapper, bot_id, botserver):
        """
        Initializes all handler with common information.

        Might remove bot_id from here later on?
        """
        HandlerFactory.botserver = botserver
        for handler in HandlerFactory.handlers:
            HandlerFactory.handlers[handler].init(slack_wrapper)

    def process(slack_wrapper, botserver, message, channel_id, user_id):
        log.debug("Processing message: {} from {} ({})".format(message, channel_id, user_id))

        try: # Parse command and check for malformed input
            command_line = unidecode(message.lower())
            args = shlex.split(command_line)
        except:
            message = "Command failed : Malformed input."
            slack_wrapper.post_message(channel_id, message)
            return

        try:
            handler_name = args[0]
            processed = False
            usage_msg = ""

            admin_users = botserver.get_config_option("admin_users")
            user_is_admin = admin_users and user_id in admin_users

            # Call a specific handler with this command
            handler = HandlerFactory.handlers.get(handler_name)

            if handler:
                # Setup usage message
                if len(args) < 2 or args[1] == "help":
                    usage_msg += handler.get_usage(user_is_admin)
                    processed = True

                else: # Send command to specified handler
                    command = args[1]
                    if handler.can_handle(command, user_is_admin):
                        handler.process(slack_wrapper, command, args[2:], channel_id, user_id, user_is_admin)
                        processed = True

            else: # Pass the command to every available handler
                command = args[0]

                for handler_name, handler in HandlerFactory.handlers.items():
                    if command == "help": # Setup usage message
                        usage_msg += "{}\n".format(handler.get_usage(user_is_admin))
                        processed = True

                    elif handler.can_handle(command, user_is_admin): # Send command to handler
                        handler.process(slack_wrapper, command,
                                        args[1:], channel_id, user_id, user_is_admin)
                        processed = True

            if not processed: # Send error message
                message = "Unknown handler or command : `{}`".format(message)
                slack_wrapper.post_message(channel_id, message)

            if usage_msg: # Send usage message
                send_help_as_dm = botserver.get_config_option("send_help_as_dm") == "1"
                target_id = user_id if send_help_as_dm else channel_id
                slack_wrapper.post_message(target_id, usage_msg)

        except InvalidCommand as e:
            slack_wrapper.post_message(channel_id, e.message)

        except Exception as ex:
            log.exception("An error has occured while processing a command")
