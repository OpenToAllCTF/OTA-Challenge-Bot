import re

from bottypes.command import *
from bottypes.command_descriptor import *
from bottypes.invalid_command import *
import handlers.handler_factory as handler_factory
from handlers.base_handler import *
from addons.syscalls.syscallinfo import *
from util.util import *


class ShowAdminsCommand(Command):
    """Shows list of users in the admin user group."""

    @classmethod
    def execute(cls, slack_wrapper, args, timestamp, channel_id, user_id, user_is_admin):
        """Execute the ShowAdmins command."""

        admin_users = handler_factory.botserver.get_config_option("admin_users")

        if admin_users:
            response = "Administrators\n"
            response += "===================================\n"

            for admin_id in admin_users:
                user_object = slack_wrapper.get_member(admin_id)

                if user_object['ok']:
                    response += "*{}* ({})\n".format(get_display_name_from_user(user_object["user"]), admin_id)

            response += "==================================="

            response = response.strip()

            if response == "":  # Response is empty
                response += "*No entries found*"

            slack_wrapper.post_message(channel_id, response)
        else:
            response = "No admin_users group found. Please check your configuration."

            slack_wrapper.post_message(channel_id, response)


class AddAdminCommand(Command):
    """Add a user to the admin user group."""

    @classmethod
    def execute(cls, slack_wrapper, args, timestamp, channel_id, user_id, user_is_admin):
        """Execute the AddAdmin command."""
        user_object = resolve_user_by_user_id(slack_wrapper, args[0])

        admin_users = handler_factory.botserver.get_config_option("admin_users")

        if user_object['ok'] and admin_users:
            if user_object['user']['id'] not in admin_users:
                admin_users.append(user_object['user']['id'])

                handler_factory.botserver.set_config_option("admin_users", admin_users)

                response = "User *{}* added to the admin group.".format(user_object['user']['name'])
                slack_wrapper.post_message(channel_id, response)
            else:
                response = "User *{}* is already in the admin group.".format(user_object['user']['name'])
                slack_wrapper.post_message(channel_id, response)
        else:
            response = "User *{}* not found. You must provide the slack user id, not the username.".format(args[0])
            slack_wrapper.post_message(channel_id, response)


class RemoveAdminCommand(Command):
    """Remove a user from the admin user group."""

    @classmethod
    def execute(cls, slack_wrapper, args, timestamp, channel_id, user_id, user_is_admin):
        """Execute the RemoveAdmin command."""
        user = parse_user_id(args[0])

        admin_users = handler_factory.botserver.get_config_option("admin_users")

        if admin_users and user in admin_users:
            admin_users.remove(user)
            handler_factory.botserver.set_config_option("admin_users", admin_users)

            response = "User *{}* removed from the admin group.".format(user)
            slack_wrapper.post_message(channel_id, response)
        else:
            response = "User *{}* doesn't exist in the admin group".format(user)
            slack_wrapper.post_message(channel_id, response)


class AsCommand(Command):
    """Execute a command as another user."""

    @classmethod
    def execute(cls, slack_wrapper, args, timestamp, channel_id, user_id, user_is_admin):
        """Execute the As command."""
        dest_user = args[0].lower()
        dest_command = args[1].lower().lstrip("!")

        dest_arguments = args[2:]

        user_obj = resolve_user_by_user_id(slack_wrapper, dest_user)

        if user_obj['ok']:
            dest_user_id = user_obj['user']['id']

            # Redirecting command execution to handler factory
            handler_factory.process_command(slack_wrapper, dest_command, [
                                            dest_command] + dest_arguments, timestamp, channel_id, dest_user_id, user_is_admin)
        else:
            raise InvalidCommand("You have to specify a valid user (use @-notation).")


class AdminHandler(BaseHandler):
    """
    Handles configuration options for administrators.

    Commands :
    # Show administrator users
    !admin show_admins

    # Add a user to the administrator group
    !admin add_admin user_id

    # Remove a user from the administrator group
    !admin remove_admin user_id
    """

    def __init__(self):
        self.commands = {
            "show_admins": CommandDesc(ShowAdminsCommand, "Show a list of current admin users", None, None, True),
            "add_admin": CommandDesc(AddAdminCommand, "Add a user to the admin user group", ["user_id"], None, True),
            "remove_admin": CommandDesc(RemoveAdminCommand, "Remove a user from the admin user group", ["user_id"], None, True),
            "as": CommandDesc(AsCommand, "Execute a command as another user", ["@user", "command"], None, True)
        }


handler_factory.register("admin", AdminHandler())
