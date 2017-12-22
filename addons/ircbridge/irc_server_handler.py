"""
Handler for managing the pool of active irc bridges.
"""
import threading
import json
import jsonpickle
from addons.ircbridge.irc_server import IrcServer
from addons.ircbridge.types.irc_server_info import IrcServerInfo

from addons.ircbridge.irc_thread import IrcThread
from addons.ircbridge.types.irc_server_status import IrcServerStatus
from bottypes.message_queue_entry import MessageQueueEntry
from bottypes.message_queue import MessageQueue
from util.loghandler import log

"""
TODO:
- On adding servers, check if servers for the specific IRC server are already registered, to avoid using multiple sessions.
- Stop all threads on graceful shutdown of server.
- Maybe add a configuration for auto-reconnect to all configured bridges on bot restart.
"""

_server_dict_lock = threading.Lock()
_msg_queue_lock = threading.Lock()

_registered_servers = {}
_message_queue = None

KNOWN_SERVER_FILE = "./databases/irc_servers"
IRC_SERVER_CONFIG = "./irc_config.json"
CONFIG = None


def store_irc_servers(acquire=True):
    """
    Store currently registered irc servers and bridges.

    Args:
        acquire(bool): Acquire server dictionary lock. If not set, the calling methods must handle locking.
    """
    global _registered_servers

    lock_server_dict(acquire)

    server_info_list = []

    try:
        for server_name in _registered_servers:
            server_info_list.append(_registered_servers[server_name].info)
    finally:
        release_server_dict(acquire)

    with open(KNOWN_SERVER_FILE, "w") as f:
        f.write(jsonpickle.encode(server_info_list))


def load_irc_servers(slack_wrapper):
    """
    Load registered servers and bridges from config file.

    Args:
        slack_wrapper(obj): The slack wrapper. Used to initialize existing server/bridges with the current slack connection.
    """
    global _registered_servers

    server_info_list = []

    # Load servers/bridges from file
    try:
        with open(KNOWN_SERVER_FILE) as f:
            data = f.read().strip()

            if data:
                server_info_list = jsonpickle.decode(data)
    except FileNotFoundError:
        log.info("No server config file found. Initializing new list.")
        _registered_servers = {}

    lock_server_dict()

    # Register found servers/bridges with handler
    try:
        _registered_servers = {}

        for server_info in server_info_list:
            _registered_servers[server_info.name] = IrcServer(slack_wrapper, server_info, CONFIG)
    finally:
        release_server_dict()


def lock_msg_queue(acquire=True):
    """
    Acquire lock for working with global message queue.

    Args:
        acquire: Acquire the lock. If set to false, this method will do nothing and assume,
                  that a calling method already handles the lock acquisition.
    """
    if acquire:
        _msg_queue_lock.acquire()


def release_msq_queue(acquire=True):
    """
    Release global lock for message queue.

    Args:
        release: Release the lock. If set fo false, this method will do nothing and assume,
                  that a calling method already handles the lock release.
    """
    if acquire:
        _msg_queue_lock.release()


def lock_server_dict(acquire=True):
    """
    Acquire lock for working with global (not thread - safe) bridge dictionary.

    Args:
        acquire: Acquire the lock. If set to false, this method will do nothing and assume,
                  that a calling method already handles the lock acquisition.
    """
    if acquire:
        _server_dict_lock.acquire()


def release_server_dict(release=True):
    """
    Release global lock for bridge dictionary.

    Args:
        release: Release the lock. If set fo false, this method will do nothing and assume,
                  that a calling method already handles the lock release.
    """
    if release:
        log.info("Releasing bridge lock.")
        _server_dict_lock.release()


def initialize_server_handler(slack_wrapper):
    """
    Initialize the IrcBridgeHandler.

    Args:
        slack_wrapper(obj): The slack wrapper for current slack connection.
    """
    global CONFIG, _message_queue

    log.info("Loading IRC server configuration and initialize server handler.")
    with open(IRC_SERVER_CONFIG) as f:
        CONFIG = json.load(f)

    lock_server_dict()

    try:
        # If bot reconnected, stop possible running threads gracefully.
        if _registered_servers:
            for server in _registered_servers.values():
                for bridge in server.info.bridges:
                    server.disconnect_bridge(bridge)
                server.do_disconnect()
    finally:
        release_server_dict()

    load_irc_servers(slack_wrapper)

    lock_msg_queue()

    try:
        log.info("Initialize message queue for IRC server handler.")

        # if a message queue thread exist, stop and recreate a new for new slack_wrapper
        if _message_queue:
            _message_queue.stop()

        use_queue = CONFIG["use_message_queue"] == "True"
        queue_interval = int(CONFIG["message_queue_interval"])

        _message_queue = MessageQueue(slack_wrapper, use_queue, queue_interval)
        _message_queue.start()
    finally:
        release_msq_queue()


def push_irc_bridge_msg(channel_id, category, sender, channel, message):
    """
    Pushes a message to the global message queue.

    Args:
        channel_id(int): The ID of the destination slack channel.
        category(str): The category for this message.
        sender(str): The name of the sender of this message.
        message(str): The message to send.
    """
    global _message_queue

    if channel:
        _message_queue.add_message(MessageQueueEntry(channel_id, category, "<{}> {}".format(sender, channel), message))
    else:
        _message_queue.add_message(MessageQueueEntry(channel_id, category, "<{}>".format(sender), message))


def push_slack_message(slack_wrapper, channel_id, sender, message):
    """
    Send a message to a slack channel.

    Args:
        slack_wrapper(obj): The slack wrapper for the current slack connection.
        channel_id(int): The ID of the destination slack channel.
        sender(str): The name of the sender of this message.
        message(str): The message to send.
    """
    msg = "_IRC_ *<{}>*: {}".format(sender, message)
    slack_wrapper.post_message(channel_id, msg)


def push_slack_bridge_system_message(slack_wrapper, bridge, sender, message):
    """
    Send a system message to a the slack channel of a specific bridge.

    Args:
        slack_wrapper(obj): The slack wrapper for the current slack connection.
        bridge(obj): The bridge object to which the message should be sent.
        sender(str): The name of the sender of this message.
        message(str): The message to send.
    """
    push_slack_message(slack_wrapper, bridge.slack_channel_id, sender, message)


def push_slack_bridge_message(bridge, sender, message):
    """
    Send a message from an IRC channel to a specific bridge.

    Args:
        bridge(obj): The bridge object to which the message should be sent.
        sender(str): The name of the sender of this message.
        message(str): The message to send.
    """
    push_irc_bridge_msg(bridge.slack_channel_id, "IRC", sender, bridge.irc_channel, message)


def add_irc_server(server_name, slack_wrapper, irc_server, irc_port, irc_nick, irc_realname):
    """
    Register a new irc server to the list of known servers.

    Args:
        server_name(str): The name for the server object.
        slack_wrapper(obj): The slack wrapper for the current slack connection.
        irc_server(str): The irc server for this bridge(e.g. irc.freenode.org).
        irc_nick(str): The nick to use on that irc server.
        irc_realname(str): The real name to use on that irc server.
    """

    lock_server_dict()

    try:
        # Check if the server already exists.
        if server_name in _registered_servers:
            return False, "IRC server *{}* already exists.".format(server_name)

        # Add the server to the global dictionary
        if irc_server.startswith("<") and irc_server.endswith(">"):
            irc_server = irc_server[2:-1]

            if "|" in irc_server:
                irc_server = irc_server.split("|")[1]

        server_info = IrcServerInfo(server_name, irc_server, irc_port, irc_nick, irc_realname)
        server = IrcServer(slack_wrapper, server_info, CONFIG)

        _registered_servers[server_name] = server

        store_irc_servers(False)

        return True, "IRC server *{}* registered.".format(server_name)
    except:
        log.exception("Error on adding the irc server (%s / %s:%d).", server_name, irc_server, irc_port)
        return False, "Sorry, couldn't register the irc server. Please check the server logs."
    finally:
        release_server_dict()


def get_registered_servers():
    """
    Return information about the currently registered irc servers.
    """
    lock_server_dict()

    try:
        return [server.info for server in _registered_servers.values()]
    finally:
        release_server_dict()


def connect_irc_server(server_name, origin_slack_channel_id):
    """
    Start the corresponding irc server thread and connect to the irc server.

    Args:
        server_name(str): Name of the server to start.
        origin_slack_channel_id(str): ID of the slack channel, in which this command was executed.
    """
    lock_server_dict()

    try:
        if server_name not in _registered_servers:
            return False, "IRC server *{}* not found.".format(server_name)

        server = _registered_servers[server_name]

        if server.info.status == IrcServerStatus.CONNECTED:
            return False, "IRC server *{}* is already connected.".format(server_name)
        if server.info.status == IrcServerStatus.CONNECTING or server.info.status == IrcServerStatus.AUTHENTICATING:
            return False, "IRC server *{}* is already connecting.".format(server_name)

        server.info.status = IrcServerStatus.CONNECTING

        server.thread = IrcThread(server, origin_slack_channel_id)
        server.thread.start()

    finally:
        release_server_dict()

    return True, ""


def disconnect_irc_server(server_name, acquire_lock=True):
    """
    Disconnect the irc server and stop the corresponding irc bridges.

    Args:
        server_name(str): Name of the server to stop.
        acquire_lock(bool): Acquire lock on server dictionary.
    """
    lock_server_dict(acquire_lock)

    try:
        if server_name in _registered_servers:
            server = _registered_servers[server_name]

            if not server.info.status == IrcServerStatus.CONNECTED:
                return False, "IRC server *{}* is not connected.".format(server_name)

            server.thread.disconnect()
    finally:
        release_server_dict(acquire_lock)

    return True, ""


def remove_irc_server(server_name, acquire_lock=True):
    """
    Remove the corresponding server from the known server list.

    Args:
        server_name(str): Name of the server to remove.
        acquire_lock(bool): Acquire lock on bridge dictionary.
    """
    lock_server_dict(acquire_lock)

    try:
        if server_name in _registered_servers:
            disconnect_irc_server(server_name, False)
            del _registered_servers[server_name]

            store_irc_servers(False)

            return True, "IRC server *{}* removed.".format(server_name)
        else:
            return False, "There is no IRC server *{}*.".format(server_name)
    finally:
        release_server_dict(acquire_lock)


def add_irc_server_bridge(server_name, bridge_name, irc_channel, slack_channel_id, slack_channel_name):
    """
    Register a bridge to a server object.

    Args:
        server_name(str): The name of the parent server.
        bridge_name(str): The name for the bridge to register.
        irc_channel(str): The IRC channel, the bridge will connect to.
        slack_channel_id(str): The ID of the slack channel, the bridge will connect to.
        slack_channel_name(str): Human readable name of the slack channel.
    """
    lock_server_dict()

    try:
        if server_name in _registered_servers:
            res = _registered_servers[server_name].add_bridge(
                bridge_name, irc_channel, slack_channel_id, slack_channel_name)

            # If bridge was added successfully, store updated server list
            if res[0]:
                store_irc_servers(False)

            return res
        else:
            return False, "There is no IRC server *{}*".format(server_name)
    finally:
        release_server_dict()


def remove_irc_server_bridge(server_name, bridge_name):
    """
    Unregister a bridge from the specified server.

    Args:
        server_name(str): The name of the server, the bridge belongs to.
        bridge_name(str): The name of the bridge to unregister.
    """
    lock_server_dict()

    try:
        if server_name in _registered_servers:
            return _registered_servers[server_name].remove_bridge(bridge_name)
        else:
            return False, "There is no IRC server *{}*".format(server_name)
    finally:
        release_server_dict()


def connect_irc_server_bridge(server_name, bridge_name):
    """
    Connect the specified bridge to the corresponding IRC channel.

    Args:
        server_name(str): The name of the server, the bridge belongs to.
        bridge_name(str): The name of the bridge to connect.
    """
    lock_server_dict()

    try:
        if server_name in _registered_servers:
            if not _registered_servers[server_name].info.status == IrcServerStatus.CONNECTED:
                return False, "The specified IRC server isn't connect. Connect to IRC first."
            else:
                return _registered_servers[server_name].connect_bridge(bridge_name)
    finally:
        release_server_dict()


def disconnect_irc_server_bridge(server_name, bridge_name):
    """
    Disconnect the specified bridge from the corresponding IRC channel.

    Args:
        server_name(str): The name of the server, the bridge belongs to.
        bridge_name(str): The name of the bridge to disconnect.
    """
    lock_server_dict()

    try:
        if server_name in _registered_servers:
            if not _registered_servers[server_name].info.status == IrcServerStatus.CONNECTED:
                return False, "The specified IRC server isn't connected."
            else:
                return _registered_servers[server_name].disconnect_bridge(bridge_name)
    finally:
        release_server_dict()
