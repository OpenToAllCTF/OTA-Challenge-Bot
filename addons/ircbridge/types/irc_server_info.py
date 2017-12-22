from addons.ircbridge.types.irc_server_status import IrcServerStatus

class IrcServerInfo:
    def __init__(self, name, irc_server, irc_port, irc_nick, irc_realname):
        """
        Information about an IRC server
        name : The name of the server object.
        irc_server : The IRC server name.
        irc_port : The IRC server port.
        irc_nick : The nick to use on this IRC server.
        irc_realname : The realname to use on this IRC server.
        """
        self.name = name
        self.irc_server = irc_server
        self.irc_port = irc_port
        self.irc_nick = irc_nick
        self.irc_realname = irc_realname

        self.status = IrcServerStatus.DISCONNECTED
        self.disconnecting = False
        self.origin_slack_channel_id = None
        self.bridges = {}

    def add_bridge(self, bridge):
        self.bridges[bridge.name] = bridge