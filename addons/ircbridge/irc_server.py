import time
import irc.bot
from addons.ircbridge.types.irc_server_status import IrcServerStatus
from addons.ircbridge.types.irc_bridge_status import IrcBridgeStatus
from addons.ircbridge.types.irc_bridge import IrcBridge
from addons.ircbridge import irc_server_handler
from util.loghandler import log


class IrcServer(irc.bot.SingleServerIRCBot):
    """
    IRC bot for connecting to an IRC server and handling the communication between the IRC server 
    and the registered bridges.
    """

    def __init__(self, slack_wrapper, server_info, config):
        self.info = server_info
        self.slack_wrapper = slack_wrapper
        self.config = config

        self.info.status = IrcServerStatus.DISCONNECTED
        self.nick_counter = 0
        self.is_running = True

        for bridge in self.info.bridges.values():
            bridge.status = IrcBridgeStatus.DISCONNECTED

        irc.bot.SingleServerIRCBot.__init__(
            self, [(self.info.irc_server, self.info.irc_port)], self.info.irc_nick, self.info.irc_realname)

    def add_bridge(self, bridge_name, irc_channel, slack_channel_id, slack_channel_name):
        """
        Register an IRC bridge with this server.

        Args:
            bridge_name(str) : The name for the bridge to register.
            irc_channel(str) : The IRC channel this bridge will be connected to.
            slack_channel_id(str) : The ID of the slack channel this bridge will be connected to.
            slack_channel_name(str) : The human readable name of the slack channel for this bridge.
        """
        self.info.bridges[bridge_name] = IrcBridge(
            bridge_name, self.info.name, irc_channel, slack_channel_id, slack_channel_name)

        return True, "Added bridge *{}/{}*".format(self.info.name, bridge_name)

    def remove_bridge(self, bridge_name):
        """
        Remove a registered IRC bridge from this server.

        Args:
            bridge_name(str) : The name of the bridge to remove.
        """
        if bridge_name in self.info.bridges:
            bridge = self.info.bridges[bridge_name]

            if bridge.status == IrcBridgeStatus.CONNECTED:
                self.leave_channel(bridge.irc_channel)

            del self.info.bridges[bridge_name]

            return True, "Removed bridge *{}/{}*".format(self.info.name, bridge_name)
        else:
            return False, "No bridge *{}/{}* found.".format(self.info.name, bridge_name)

    def push_system_message(self, message):
        """
        Send a system message to the slack channel, from which this server was started.

        Args:
            message(str) : The message to send.
        """
        irc_server_handler.push_slack_message(self.slack_wrapper, self.info.origin_slack_channel_id, "SYSTEM", message)

    def push_bridge_system_message(self, bridge, message):
        """
        Send a system message to a specific bridge.

        Args:
            bridge(obj) : The destination bridge object.
            message(str) : The message to send.
        """
        irc_server_handler.push_slack_bridge_system_message(self.slack_wrapper, bridge, "SYSTEM", message)

    def push_bridge_message(self, bridge, sender, message):
        """
        Send a message to a specific bridge via message queue.

        Args:
            bridge(obj) : The destination bridge object.
            sender(str) : The name of the sender of this message.
            message(str) : The message to send.
        """
        irc_server_handler.push_slack_bridge_message(bridge, sender, message)

    def push_system_broadcast_message(self, message):
        """
        Broadcast a message for this server. This message will be sent to originating slack channel and all bridges,
        trying to avoid sending duplicate messages.

        Args:
            message(str) : The message to broadcast.
        """
        pushed_channels = {}

        self.push_system_message(message)
        pushed_channels[self.info.origin_slack_channel_id] = True

        if self.info.bridges:
            for bridge in self.info.bridges.values():
                if not bridge.slack_channel_id in pushed_channels:
                    self.push_bridge_system_message(bridge, message)
                    pushed_channels[bridge.slack_channel_id] = True

    def do_connect(self, origin_slack_channel_id):
        """
        Initiate the connection to the IRC server.

        Args:
            origin_slack_channel_id(str) : The ID of the slack channel, from which this command was originated.
        """
        self.is_running = True

        self.info.status = IrcServerStatus.AUTHENTICATING
        self.info.origin_slack_channel_id = origin_slack_channel_id

        self.push_system_message(
            "Server *{}* starts connecting to *{}*. Please wait...".format(self.info.name, self.info.irc_server))

        self._connect()

    def do_disconnect(self):
        """
        Disconnect all registered bridges and disconnect from the IRC server.
        """
        self.info.disconnecting = True

        self.push_system_broadcast_message(
            "Server *{}* starts disconnecting from *{}*.".format(self.info.name, self.info.irc_server))

        for bridge in self.info.bridges.values():
            bridge.status = IrcBridgeStatus.DISCONNECTED

        self.disconnect()

    def connect_bridge(self, bridge_name):
        """
        Connect a bridge with an IRC channel. The server has to be connected for this.

        Args:
            bridge_name(str): The name of the bridge to connect.
        """
        if bridge_name in self.info.bridges:
            bridge = self.info.bridges[bridge_name]

            # TODO: Use the server channel list instead of the bridges to retrieve "real" status
            if bridge.status == IrcBridgeStatus.DISCONNECTED:
                self.join_channel(bridge.irc_channel)
                bridge.status = IrcBridgeStatus.CONNECTED
                return True, ""
            else:
                return False, "Bridge *{}/{}* already connected.".format(self.info.name, bridge_name)
        else:
            return False, "Bridge *{}/{}* not found.".format(self.info.name, bridge_name)

    def disconnect_bridge(self, bridge_name):
        """
        Disconnect a bridge from an IRC channel.

        Args:
            bridge_name(str): The name of the bridge to disconnect.
        """
        if bridge_name in self.info.bridges:
            bridge = self.info.bridges[bridge_name]

            if bridge.status == IrcBridgeStatus.CONNECTED:
                self.leave_channel(bridge.irc_channel)
                bridge.status = IrcBridgeStatus.DISCONNECTED
                return True, ""
            else:
                return False, "Bridge *{}/{}* isn't connected.".format(self.info.name, bridge_name)
        else:
            return False, "Bridge *{}/{}* not found.".format(self.info.name, bridge_name)

    def join_channel(self, channel):
        """
        Join an IRC channel.

        Args:
            channel(str): The name of the IRC channel to join.
        """
        self.connection.join(channel)

    def leave_channel(self, channel):
        """
        Leaves an IRC channel.

        Args:
            channel(str): The name of the IRC channel to leave.
        """
        self.connection.part(channel)

    def get_bridge_for_channel(self, channel):
        """
        Retrieves the corresponding bridge object, that's connected to the specified channel.

        Args:
            channel(str) : The IRC channel, the bridge is connected to.
        """
        for bridge in self.info.bridges.values():
            if bridge.irc_channel == channel:
                return bridge

        return None

    def on_nicknameinuse(self, conn, event):
        """Event handler for 'NicknameInUse'."""
        new_nick = "{}_{}".format(c.get_nickname(), self.nick_counter)
        self.push_system_message("Server nick already in use. Will retry with *{}*".format(new_nick))
        self.nick_counter += 1
        conn.nick(new_nick)

    def on_kick(self, conn, event):
        """Event handler for 'Kick'."""
        bridge = self.get_bridge_for_channel(event.target)

        if bridge:
            bridge.status = IrcBridgeStatus.DISCONNECTED
            self.push_bridge_system_message(
                bridge, "Bridge *{}* was kicked from channel *{}*.".format(bridge.bridge_name, event.target))

    def on_welcome(self, conn, event):
        """Event handler for 'Welcome'."""
        self.info.status = IrcServerStatus.CONNECTED

        self.push_system_message("Server *{}* connected to IRC (*{}*).".format(self.info.name, self.info.irc_server))

    def on_disconnect(self, conn, event):
        """Event handler for 'Disconnect'."""
        self.info.status = IrcServerStatus.DISCONNECTED

        self.push_system_broadcast_message("Server *{}* disconnected from IRC.".format(self.info.name))

        # Check if this was an "unplanned" disconnect
        if not self.info.disconnecting:
            self.push_system_broadcast_message(
                "Server *{}* will try to reconnect in 60 seconds.".format(self.info.name))
            return

        # Server thread should terminate after "planned" disconnect
        self.is_running = False

    def on_join(self, conn, event):
        """Event handler for 'Join'."""
        bridge = self.get_bridge_for_channel(event.target)

        if bridge:
            self.push_bridge_system_message(
                bridge, "Bridge *{}* joined channel *{}* on *{}*.".format(bridge.bridge_name, bridge.irc_channel, self.info.name))

    def on_part(self, conn, event):
        """Event handler for 'Part'."""
        bridge = self.get_bridge_for_channel(event.target)

        if bridge:
            self.push_bridge_system_message(
                bridge, "Bridge *{}* left channel *{}* on *{}*.".format(bridge.bridge_name, bridge.irc_channel, self.info.name))

    def on_pubmsg(self, conn, event):
        """Event handler for 'PubMsg'."""
        bridge = self.get_bridge_for_channel(event.target)

        if bridge:
            self.push_bridge_message(bridge, event.source.nick, event.arguments[0])
