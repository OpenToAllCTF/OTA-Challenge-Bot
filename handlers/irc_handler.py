import shlex
import pickle
import re
import json

import websocket

from unidecode import unidecode

from bottypes.command import *
from bottypes.command_descriptor import *
from handlers.handler_factory import *
from handlers.base_handler import *
from addons.ircbridge import irc_server_handler
from util.util import *


class AddIRCServerCommand(Command):
    """Add irc server to known server list."""

    def execute(self, slack_wrapper, args, channel_id, user_id):
        """Execute the AddIRCServerCommand command."""

        server_name = args[0]
        irc_server = args[1]

        irc_nick = args[2] if len(args) > 2 else "OTA"
        irc_port = try_parse_int(args[3])[0] if len(args) > 3 else 6667
        irc_realname = args[4] if len(args) > 4 else "OTA IRC Bridge"

        res = irc_server_handler.add_irc_server(
            server_name, slack_wrapper, irc_server, irc_port, irc_nick, irc_realname)

        if res[1]:
            slack_wrapper.post_message(channel_id, res[1])


class RemoveIRCServerCommand(Command):
    """Remove irc server from known server list."""

    def execute(self, slack_wrapper, args, channel_id, user_id):
        """Execute the RemoveIRCServerCommand command."""

        server_name = args[0]

        res = irc_server_handler.remove_irc_server(server_name)

        if res[1]:
            slack_wrapper.post_message(channel_id, res[1])


class ConnectIRCServerCommand(Command):
    """Connect an IRC bridge to the specified IRC server/channel."""

    def execute(self, slack_wrapper, args, channel_id, user_id):
        """Execute the StartIRC command."""

        server_name = args[0]

        res = irc_server_handler.connect_irc_server(server_name, channel_id)

        if res[1]:
            slack_wrapper.post_message(channel_id, res[1])


class DisconnectIRCServerCommand(Command):
    """Disconnect an IRC bridge from IRC."""

    def execute(self, slack_wrapper, args, channel_id, user_id):
        """Execute the StopIRC command."""

        server_name = args[0]

        res = irc_server_handler.disconnect_irc_server(server_name, channel_id)

        if res[1]:
            slack_wrapper.post_message(channel_id, res[1])


class AddIRCCommand(Command):
    """Add irc bridge to current channel."""

    def execute(self, slack_wrapper, args, channel_id, user_id):
        """Execute the AddIRC command."""

        server_name = args[0]
        bridge_name = args[1]
        channel_name = args[2]

        slack_channel = slack_wrapper.get_channel_info(channel_id)

        res = irc_server_handler.add_irc_server_bridge(
            server_name, bridge_name, channel_name, channel_id, slack_channel['channel']['name'])

        if res[1]:
            slack_wrapper.post_message(channel_id, res[1])


class RemoveIRCCommand(Command):
    """Stop and remove specified irc bridge."""

    def execute(self, slack_wrapper, args, channel_id, user_id):
        """Execute the RemoveIRC command."""

        server_name = args[0]
        bridge_name = args[1]

        res = irc_server_handler.remove_irc_server_bridge(server_name, bridge_name)

        if res[1]:
            slack_wrapper.post_message(channel_id, res[1])


class StartIRCCommand(Command):
    """Connect an IRC bridge to the specified IRC server/channel."""

    def execute(self, slack_wrapper, args, channel_id, user_id):
        """Execute the StartIRC command."""

        server_name = args[0]
        bridge_name = args[1]

        res = irc_server_handler.connect_irc_server_bridge(server_name, bridge_name)

        if res[1]:
            slack_wrapper.post_message(channel_id, res[1])


class StopIRCCommand(Command):
    """Disconnect an IRC bridge from IRC."""

    def execute(self, slack_wrapper, args, channel_id, user_id):
        """Execute the StopIRC command."""

        server_name = args[0]
        bridge_name = args[1]

        res = irc_server_handler.disconnect_irc_server_bridge(server_name, bridge_name)

        if res[1]:
            slack_wrapper.post_message(channel_id, res[1])


class IRCStatusCommand(Command):
    """Shows a list of currently registered bridges."""

    def execute(self, slack_wrapper, args, channel_id, user_id):
        """Execute the IRCStatusCommand command."""

        server_list = irc_server_handler.get_registered_servers()

        message = ""

        if server_list:
            for server in server_list:
                message += "*============= {} ({}) =============*\n".format(server.name, server.irc_server)
                message += "*Status* : {}\n".format(server.status)
                message += "\n"

                if server.bridges:
                    for bridge_key in server.bridges:
                        bridge = server.bridges[bridge_key]

                        message += "*{}* - IRC: {} <-> Slack: {} ({})\n".format(
                            bridge.bridge_name, bridge.irc_channel, bridge.slack_channel_name, bridge.status)
                else:
                    message += "No bridges configured for this server."
        else:
            message = "There are no registered IRC servers at the moment."

        slack_wrapper.post_message(channel_id, message, "")


class IrcHandler(BaseHandler):
    """Handle irc update threads for creating irc bridges in slack channels."""

    def __init__(self):
        self.commands = {
            "addserver": CommandDesc(AddIRCServerCommand, "Register an IRC server to the known server list", ["server_name", "irc_server"], ["irc_nick", "irc_port"], True),
            "rmserver": CommandDesc(RemoveIRCServerCommand, "Remove an IRC server from the known server list (Caution: this will remove all connected bridges also)", ["server_name"], None, True),
            "startserver": CommandDesc(ConnectIRCServerCommand, "Connect the specified server thread to the IRC server", ["server_name"], None, True),
            "stopserver": CommandDesc(DisconnectIRCServerCommand, "Disconnect the specified server from IRC (and all connected bridges)", ["server_name"], None, True),
            "addirc": CommandDesc(AddIRCCommand, "Add an IRC bridge to the current channel", ["server_name", "bridge_name", "irc_channel"], None, True),
            "rmirc": CommandDesc(RemoveIRCCommand, "Remove an IRC bridge from slack", ["server_name", "bridge_name"], None, True),
            "startirc": CommandDesc(StartIRCCommand, "Connect a registered IRC bridge", ["server_name", "bridge_name"], None, True),
            "stopirc": CommandDesc(StopIRCCommand, "Disconnect a registered IRC bridge", ["server_name", "bridge_name"], None, True),
            "ircstatus": CommandDesc(IRCStatusCommand, "Shows a list of currently registered irc bridges", None, None)
        }

    def init(self, slack_wrapper):
        irc_server_handler.initialize_server_handler(slack_wrapper)


HandlerFactory.register("irc", IrcHandler())
