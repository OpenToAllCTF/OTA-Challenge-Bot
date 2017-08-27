from abc import ABC, abstractmethod

from bottypes.command import *
from bottypes.invalid_command import *


class BaseHandler(ABC):

    def canHandle(self, command):
        if command in self.commands:
            return True

        return False

    def init(self, slack_client, botid):
        pass

    # TODO: Refactor showCommandUsage and showHandlerUsage, so they'll reuse
    # duplicate code
    def getCommandUsage(self, command, descriptor):
        msg = "Usage: `!%s %s" % (self.handler_name, command)

        if descriptor.arguments:
            for arg in descriptor.arguments:
                msg += " <%s>" % arg

        if descriptor.optionalArgs:
            for arg in descriptor.optionalArgs:
                msg += " [%s]" % arg

        if descriptor.description:
            msg += "\t(%s)" % descriptor.description

        msg += "`"

        return msg

    def getHandlerUsage(self, slack_client):
        msg = "```"

        for command in self.commands:
            cmdMsg = "!%s %s" % (self.handler_name, command)

            descriptor = self.commands[command]

            if descriptor.arguments:
                for arg in descriptor.arguments:
                    cmdMsg += " <%s>" % arg

            if descriptor.optionalArgs:
                for arg in descriptor.optionalArgs:
                    cmdMsg += " [%s]" % arg

            msg += "%s\n" % cmdMsg

        msg += "```\n"

        return msg

    def process(self, slack_client, command, args, channel, user):
        # Check if enough arguments were passed for this command
        cmdDescriptor = self.commands[command]

        if cmdDescriptor:
            if (cmdDescriptor.arguments) and (len(args) < len(cmdDescriptor.arguments)):
                raise InvalidCommand(
                    self.getCommandUsage(command, cmdDescriptor))
            else:
                cmdDescriptor.command().execute(slack_client, args, channel, user)
