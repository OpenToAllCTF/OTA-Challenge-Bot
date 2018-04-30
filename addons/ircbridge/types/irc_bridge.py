from addons.ircbridge.types.irc_bridge_status import IrcBridgeStatus


class IrcBridge:
    def __init__(self, bridge_name, server_name, irc_channel, slack_channel_id, slack_channel_name):
        """
        An object representation of an irc bridge.
        bridge_name : The name of the bridge object.
        server_name : The name of the server object.
        irc_channel : The name of the irc channel for the bridge.
        slack_channel_id : The ID of the slack channel for the bridge.
        slack_channel_name : The human readable name of the slack channel for the bridge.
        """
        self.bridge_name = bridge_name
        self.server_name = server_name
        self.slack_channel_id = slack_channel_id
        self.slack_channel_name = "#{}".format(slack_channel_name)

        if not irc_channel.startswith("#"):
            self.irc_channel = "#{}".format(irc_channel)
        else:
            self.irc_channel = irc_channel

        self.status = IrcBridgeStatus.DISCONNECTED
