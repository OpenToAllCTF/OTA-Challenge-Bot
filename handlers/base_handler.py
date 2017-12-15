from abc import ABC, abstractmethod

from bottypes.command import *
from bottypes.invalid_command import *


class BaseHandler(ABC):

    def can_handle(self, command):
        return command in self.commands

    def init(self, slack_wrapper):
        pass

    def parse_command_usage(self, command, descriptor):
        """Returns a usage string from a given command and descriptor."""
        msg = command
        if descriptor.arguments:
            for arg in descriptor.arguments:
                msg += " <{}>".format(arg)

        if descriptor.optionalArgs:
            for arg in descriptor.optionalArgs:
                msg += " [{}]".format(arg)

        if descriptor.description:
            msg += "\t({})".format(descriptor.description)

        return msg


    def command_usage(self, command, descriptor):
        """Return the usage of a given command of a handler."""
        usage = self.parse_command_usage(command, descriptor)
        return "Usage: `!{} {}`".format(self.handler_name, usage)

    @property
    def usage(self):
        """Return the usage of a handler."""
        msg = "```"

        for command in self.commands:
            descriptor = self.commands[command]
            usage = self.parse_command_usage(command, descriptor)
            msg += "!{} {}\n".format(self.handler_name, usage)

        msg += "```"

        return msg

    def process(self, slack_wrapper, command, args, channel, user):
        """Check if enough arguments were passed for this command."""
        cmd_descriptor = self.commands[command]

        if cmd_descriptor:
            if (cmd_descriptor.arguments) and (len(args) < len(cmd_descriptor.arguments)):
                raise InvalidCommand(
                    self.command_usage(command, cmd_descriptor))
            else:
                cmd_descriptor.command().execute(slack_wrapper, args, channel, user)
