import threading
import time
from util.loghandler import log


class IrcThread(threading.Thread):
    def __init__(self, server, origin_slack_channel_id):
        log.info("IrcThread::init ({} - {}:{} @{} ({}))".format(server.info.name, server.info.irc_server,
                                                                server.info.irc_port, server.info.irc_nick, server.info.irc_realname))
        self.server = server
        self.origin_slack_channel_id = origin_slack_channel_id

        threading.Thread.__init__(self)

    def run(self):
        self.server.do_connect(self.origin_slack_channel_id)

        process_interval = int(self.server.config["irc_process_interval"])

        while self.server.is_running:
            time.sleep(process_interval)
            self.server.reactor.process_once()

        log.info("Thread exited gracefully for server {}".format(self.server.info.name))

    def disconnect(self):
        """
        Request the server object to disconnect gracefully.
        """
        self.server.do_disconnect()
