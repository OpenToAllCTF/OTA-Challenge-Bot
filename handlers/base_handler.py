from abc import ABC, abstractmethod

from bottypes.command import *
from bottypes.invalid_command import *


class BaseHandler(ABC):

    def can_handle(self, command, user_is_admin):
        cmd_available = command in self.commands

        # Check if this is an admin command and hide it for normal users
        if cmd_available:
            cmd_desc = self.commands[command]
            if (not cmd_desc.is_admin_cmd) or user_is_admin:
                return True

        return False

    def init(self, slack_wrapper):
        pass

    def parse_command_usage(self, command, descriptor):
        """Returns a usage string from a given command and descriptor."""
        msg = command
        if descriptor.arguments:
            for arg in descriptor.arguments:
                msg += " <{}>".format(arg)

        if descriptor.opt_arguments:
            for arg in descriptor.opt_arguments:
                msg += " [{}]".format(arg)

        if descriptor.description:
            msg += "\t({})".format(descriptor.description)

        return msg

    def command_usage(self, command, descriptor):
        """Return the usage of a given command of a handler."""
        usage = self.parse_command_usage(command, descriptor)
        return "Usage: `!{} {}`".format(self.handler_name, usage)

    def get_usage(self, user_is_admin):
        """Return the usage of a handler."""
        msg = "```"

        for command in self.commands:
            descriptor = self.commands[command]

            if (not descriptor.is_admin_cmd) or user_is_admin:
                usage = self.parse_command_usage(command, descriptor)
                msg += "!{} {}\n".format(self.handler_name, usage)

        msg += "```"

        # Return empty message, if no applicable commands were found
        if msg == "``````":
            return ""

        return msg

    def process(self, slack_wrapper, command, args, channel, user, user_is_admin):
        """Check if enough arguments were passed for this command."""
        cmd_descriptor = self.commands[command]

        if cmd_descriptor:
            if cmd_descriptor.arguments and len(args) < len(cmd_descriptor.arguments):
                raise InvalidCommand(
                    self.command_usage(command, cmd_descriptor))
            else:
                cmd_descriptor.command().execute(slack_wrapper, args, channel, user)
