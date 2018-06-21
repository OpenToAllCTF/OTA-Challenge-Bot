from bottypes.command import *
from bottypes.command_descriptor import *
from bottypes.invalid_command import *
import handlers.handler_factory as handler_factory
from handlers.base_handler import *
from addons.syscalls.syscallinfo import *


class ShowAvailableArchCommand(Command):
    """Shows the available architecture tables for syscalls."""

    @classmethod
    def execute(cls, slack_wrapper, args, channel_id, user_id):
        """Execute the ShowAvailableArch command."""
        archList = SyscallsHandler.syscallInfo.getAvailableArchitectures()

        msg = "\n"
        msg += "Available architectures:```"

        for arch in archList:
            msg += "{}\t".format(arch)

        msg = msg.strip() + "```"

        slack_wrapper.post_message(channel_id, msg)


class ShowSyscallCommand(Command):
    """Shows information about the requested syscall."""

    @classmethod
    def send_message(cls, slack_wrapper, channel_id, user_id, msg):
        """Send message to user or channel."""
        dest_channel = channel_id if (SyscallsHandler.MSGMODE == 0) else user_id
        slack_wrapper.post_message(dest_channel, msg)

    @classmethod
    def parse_syscall_info(cls, syscall_entries):
        """Parse syscall information."""
        msg = "```"

        for entry in syscall_entries:
            msg += "{:15} : {}\n".format(entry, syscall_entries[entry])

        return msg.strip() + "```"

    @classmethod
    def execute(cls, slack_wrapper, args, channel_id, user_id):
        """Execute the ShowSyscall command."""
        archObj = SyscallsHandler.syscallInfo.getArch(args[0].lower())

        if archObj:
            entry = None

            # convenience : Try to search syscall by id or by name, depending on what
            # the user has specified
            try:
                syscallID = int(args[1])
                entry = archObj.getEntryByID(syscallID)
            except:
                entry = archObj.getEntryByName(args[1].lower())

            if entry:
                cls.send_message(slack_wrapper, channel_id,
                                 user_id, cls.parse_syscall_info(entry))
            else:
                cls.send_message(slack_wrapper, channel_id, user_id,
                                 "Specified syscall not found: `{} (Arch: {})`".format(args[1], args[0]))
        else:
            cls.send_message(slack_wrapper, channel_id, user_id,
                             "Specified architecture not available: `{}`".format(args[0]))


class SyscallsHandler(BaseHandler):
    """
    Shows information about syscalls for different architectures.

    Commands :
    # Show available architectures
    @ota_bot syscalls available

    # Show syscall information
    @ota_bot syscalls show x86 execve
    @ota_bot syscalls show x86 11
    """

    # Specify the base directory, where the syscall tables are located
    BASEDIR = "addons/syscalls/tables"

    # Specify if messages from syscall handler should be posted to channel (0)
    # or per dm (1)
    MSGMODE = 0

    syscallInfo = None

    def __init__(self):
        SyscallsHandler.syscallInfo = SyscallInfo(SyscallsHandler.BASEDIR)

        self.commands = {
            "available": CommandDesc(ShowAvailableArchCommand, "Shows the available syscall architectures", None, None),
            "show": CommandDesc(ShowSyscallCommand, "Show information for a specific syscall", ["arch", "syscall name/syscall id"], None),
        }

handler_factory.register("syscalls", SyscallsHandler())
