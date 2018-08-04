from abc import ABC, abstractmethod

from bottypes.command import *
from bottypes.invalid_command import *


class BaseHandler(ABC):
    commands = {}  # Overridden by concrete class
    reactions = {}
    handler_name = ""  # Overridden by concrete class

    def can_handle(self, command, user_is_admin):
        if command in self.commands:
            cmd_desc = self.commands[command]
            # Hide admin commands
            if user_is_admin or not cmd_desc.is_admin_cmd:
                return True

        return False

    def can_handle_reaction(self, reaction):
        if reaction in self.reactions:
            return True
        return False

    def init(self, slack_wrapper):
        pass

    def parse_command_usage(self, command, descriptor):
        """Returns a usage string from a given command and descriptor."""
        msg = "`!{} {}".format(self.handler_name, command)

        for arg in descriptor.arguments:
            msg += " <{}>".format(arg)

        for arg in descriptor.opt_arguments:
            msg += " [{}]".format(arg)

        msg += "`"

        if descriptor.description:
            msg += "\n\t({})".format(descriptor.description)

        return msg

    def command_usage(self, command, descriptor):
        """Return the usage of a given command of a handler."""
        usage = self.parse_command_usage(command, descriptor)
        return "Usage: {}".format(usage)

    def get_usage(self, user_is_admin):
        """Return the usage of a handler."""
        msg = ""

        for command in self.commands:
            descriptor = self.commands[command]

            if (not descriptor.is_admin_cmd) or user_is_admin:
                usage = self.parse_command_usage(command, descriptor)
                msg += "{}\n".format(usage)

        # Return empty message, if no applicable commands were found
        if msg == "``````":
            return ""

        return msg

    def process(self, slack_wrapper, command, args, channel, user, user_is_admin):
        """Check if enough arguments were passed for this command."""
        cmd_descriptor = self.commands[command]

        if cmd_descriptor:
            if len(args) < len(cmd_descriptor.arguments):
                raise InvalidCommand(self.command_usage(command, cmd_descriptor))
            cmd_descriptor.command.execute(slack_wrapper, args, channel, user, user_is_admin)

    def process_reaction(self, slack_wrapper, reaction, channel, timestamp, user, user_is_admin):
        reaction_descriptor = self.reactions[reaction]

        if reaction_descriptor:
            reaction_descriptor.command.execute(
                slack_wrapper, {"reaction": reaction, "timestamp": timestamp}, channel, user, user_is_admin)
