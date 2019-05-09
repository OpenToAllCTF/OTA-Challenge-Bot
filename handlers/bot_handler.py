from bottypes.command import Command
from bottypes.command_descriptor import CommandDesc
from bottypes.invalid_command import InvalidCommand
from handlers import handler_factory
from handlers.base_handler import BaseHandler
from util.githandler import GitHandler
from util.loghandler import log
import subprocess


class PingCommand(Command):
    """Ping this server to check for uptime."""

    @classmethod
    def execute(cls, slack_wrapper, args, timestamp, channel_id, user_id, user_is_admin):
        """Announce the bot's presence in the channel."""
        slack_wrapper.post_message(channel_id, "Pong!")


class IntroCommand(Command):
    """Show an introduction message for new members."""

    @classmethod
    def execute(cls, slack_wrapper, args, timestamp, channel_id, user_id, user_is_admin):
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

    @classmethod
    def execute(cls, slack_wrapper, args, timestamp, channel_id, user_id, user_is_admin):
        """Execute the Version command."""
        try:
            message = GitHandler(".").get_version()

            slack_wrapper.post_message(channel_id, message)
        except:
            log.exception("BotHandler::VersionCommand")
            raise InvalidCommand(
                "Sorry, couldn't retrieve the git information for the bot...")


class InviteCommand(Command):
    """
    Invite a list of members to the current channel, ignores members already
    present.
    """

    @classmethod
    def execute(cls, slack_wrapper, args, timestamp, channel_id, user_id, user_is_admin):
        current_members = slack_wrapper.get_channel_members(channel_id)
        # strip uid formatting
        invited_users = [user.strip("<>@") for user in args]
        # remove already present members
        invited_users = [
            user for user in invited_users if user not in current_members]
        failed_users = []
        for member in invited_users:
            if not slack_wrapper.invite_user(member, channel_id)["ok"]:
                failed_users.append(member)

        if failed_users:
            log.exception("BotHandler::InviteCommand")
            raise InvalidCommand(
                "Sorry, couldn't invite the following members to the channel: " + ' '.join(failed_users))


class SysInfoCommand(Command):
    """
    Show information about system resources on the machine, otabot is running on.
    """

    @classmethod
    def execute(cls, slack_wrapper, args, timestamp, channel_id, user_id, user_is_admin):
        result = b"```\n"
        result += b'\n'.join(subprocess.check_output(['top', '-bn1']).split(b"\n")[:15])
        result += b"\n\n"
        result += subprocess.check_output(['df', '-h'])
        result += b"```\n"

        slack_wrapper.post_message(user_id, result)


class BotHandler(BaseHandler):
    """Handler for generic bot commands."""

    def __init__(self):
        self.commands = {
            "ping": CommandDesc(PingCommand, "Ping the bot", None, None),
            "intro": CommandDesc(IntroCommand, "Show an introduction message for new members", None, None),
            "version": CommandDesc(VersionCommand, "Show git information about the running version of the bot", None, None),
            "invite": CommandDesc(InviteCommand, "Invite a list of members (using @username) to the current channel (smarter than /invite)", ["user_list"], None),
            "sysinfo": CommandDesc(SysInfoCommand, "Show system information", None, None, True)
        }


handler_factory.register("bot", BotHandler())
