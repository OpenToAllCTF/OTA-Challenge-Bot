from bottypes.command import *
from bottypes.command_descriptor import *
from bottypes.invalid_command import *
from handlers.handler_factory import *
from handlers.base_handler import *
from addons.syscalls.syscallinfo import *
from util.util import *

import re


class ShowAdminsCommand(Command):
    """Shows list of users in the admin user group."""

    def execute(self, slack_wrapper, args, channel_id, user_id):
        """Execute the ShowAdmins command."""

        admin_users = HandlerFactory.botserver.get_config_option("admin_users")

        if admin_users:
            response = "Administrators\n"
            response += "===================================\n"

            for admin_id in admin_users:
                user_object = slack_wrapper.get_member(admin_id)

                if user_object['ok']:
                    response += "*{}* ({})\n".format(
                        user_object['user']['name'], admin_id)

            response += "==================================="

            response = response.strip()

            if response == "":  # Response is empty
                response += "*No entries found*"

            AdminHandler.send_message(
                slack_wrapper, channel_id, user_id, response)
        else:
            response = "No admin_users group found. Please check your configuration."

            AdminHandler.send_message(
                slack_wrapper, channel_id, user_id, response)


class AddAdminCommand(Command):
    """Add a user to the admin user group."""

    def execute(self, slack_wrapper, args, channel_id, user_id):
        """Execute the AddAdmin command."""
        user_object = resolve_user_by_user_id(slack_wrapper, args[0])

        admin_users = HandlerFactory.botserver.get_config_option("admin_users")

        if user_object['ok'] and admin_users:
            if user_object['user']['id'] not in admin_users:
                admin_users.append(user_object['user']['id'])

                HandlerFactory.botserver.set_config_option(
                    "admin_users", admin_users)

                response = "User *{}* added to the admin group.".format(
                    user_object['user']['name'])
                AdminHandler.send_message(
                    slack_wrapper, channel_id, user_id, response)
            else:
                response = "User *{}* is already in the admin group.".format(
                    user_object['user']['name'])
                AdminHandler.send_message(
                    slack_wrapper, channel_id, user_id, response)
        else:
            response = "User *{}* not found. You must provide the slack user id, not the username.".format(
                args[0])
            AdminHandler.send_message(
                slack_wrapper, channel_id, user_id, response)


class RemoveAdminCommand(Command):
    """Remove a user from the admin user group."""

    def execute(self, slack_wrapper, args, channel_id, user_id):
        """Execute the RemoveAdmin command."""
        user = parse_user_id(args[0])

        admin_users = HandlerFactory.botserver.get_config_option("admin_users")

        if admin_users and user in admin_users:
            admin_users.remove(user)
            HandlerFactory.botserver.set_config_option(
                "admin_users", admin_users)

            response = "User *{}* removed from the admin group.".format(user)
            AdminHandler.send_message(
                slack_wrapper, channel_id, user_id, response)
        else:
            response = "User *{}* doesn't exist in the admin group".format(
                user)
            AdminHandler.send_message(
                slack_wrapper, channel_id, user_id, response)


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

    # Specify if messages from syscall handler should be posted to channel (0)
    # or per dm (1)
    MSG_MODE = 0

    @staticmethod
    def send_message(slack_wrapper, channel_id, user_id, msg):
        """Send message to user or channel, depending on configuration."""
        dest_channel = channel_id if AdminHandler.MSG_MODE == 0 else user_id
        slack_wrapper.post_message(dest_channel, msg)

    def __init__(self):
        self.commands = {
            "show_admins": CommandDesc(ShowAdminsCommand, "Show a list of current admin users", None, None, True),
            "add_admin": CommandDesc(AddAdminCommand, "Add a user to the admin user group", ["user_id"], None, True),
            "remove_admin": CommandDesc(RemoveAdminCommand, "Remove a user from the admin user group", ["user_id"], None, True)
        }


HandlerFactory.register("admin", AdminHandler())
