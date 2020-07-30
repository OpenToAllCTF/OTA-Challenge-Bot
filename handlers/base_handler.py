from abc import ABC

from bottypes.invalid_command import InvalidCommand
from handlers import handler_factory


class BaseHandler(ABC):
    commands = {}  # Overridden by concrete class
    aliases = {}   # Overridden by concrete class
    reactions = {}
    handler_name = ""  # Overridden by concrete class

    def can_handle(self, command, user_is_admin):
        if command in self.commands:
            cmd_desc = self.commands[command]
            # Hide admin commands
            if user_is_admin or not cmd_desc.is_admin_cmd:
                return True

        if command in self.aliases:
            if self.can_handle(self.aliases[command], user_is_admin):
                return True

        return False

    def can_handle_reaction(self, reaction):
        if reaction in self.reactions:
            return True
        return False

    def init(self, slack_wrapper):
        pass

    def get_aliases_for_command(self, command):
        cmd_aliases = []

        if self.aliases:
            for alias in self.aliases:
                if self.aliases[alias] == command:
                    cmd_aliases.append(alias)

        if cmd_aliases:
            return " `(Alias: {})`".format(", ".join(cmd_aliases))

        return ""

    def parse_command_usage(self, command, descriptor):
        """Returns a usage string from a given command and descriptor."""
        msg = "`!{} {}".format(self.handler_name, command)

        for arg in descriptor.arguments:
            msg += " <{}>".format(arg)

        for arg in descriptor.opt_arguments:
            msg += " [{}]".format(arg)

        msg += "`"

        # check for aliases
        msg += self.get_aliases_for_command(command)

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

    def process(self, slack_wrapper, command, args, timestamp, channel, user, user_is_admin):
        if handler_factory.botserver.get_config_option("maintenance_mode") and not user_is_admin:
            raise InvalidCommand("Down for maintenance, back soon.")

        """Check if enough arguments were passed for this command."""
        if command in self.aliases:
            self.process(slack_wrapper, self.aliases[command], args, timestamp, channel, user, user_is_admin)
        elif command in self.commands:
            cmd_descriptor = self.commands[command]

            if cmd_descriptor:
                if len(args) < len(cmd_descriptor.arguments):
                    raise InvalidCommand(self.command_usage(command, cmd_descriptor))
                cmd_descriptor.command.execute(slack_wrapper, args, timestamp, channel, user, user_is_admin)

    def process_reaction(self, slack_wrapper, reaction, channel, timestamp, user, user_is_admin):
        if handler_factory.botserver.get_config_option("maintenance_mode") and not user_is_admin:
            raise InvalidCommand("Down for maintenance, back soon.")

        reaction_descriptor = self.reactions[reaction]

        if reaction_descriptor:
            reaction_descriptor.command.execute(
                slack_wrapper, {"reaction": reaction, "timestamp": timestamp}, timestamp, channel, user, user_is_admin)
