# OTA Challenge Bot

The OTA challenge bot is a helper tool to be used during CTF events
through the Slack platform.

## Features

Main features :
- Tracking CTFs
- Tracking CTF challenges
- Tracking member participation in challenges
- Annoucements upon solving a challenge
- IRC bridge for getting updates from CTF IRC channels

Secondary features :
- Syscall table for arm, armthumb, x64 and x86

## Usage

```
!ctf addctf <ctf_name>
!ctf addchallenge <challenge_name>
!ctf workon <challenge_name>
!ctf status
!ctf solve <challenge_name> [support_member]
!ctf addcreds <ctf_user> <ctf_pw> (Add credentials for ctf)
!ctf showcreds (Shows credentials for current ctf)
```
```
!syscalls available
!syscalls show <arch> <syscall name/syscall id>
```
```
!bot ping
```
```
!admin show_admins    (Show a list of current admin users)
!admin add_admin <user_id>    (Add an user to the admin user group)
!admin remove_admin <user_id>    (Remove an user from the admin user group)
```
```
!irc addserver <server_name> <irc_server> [irc_nick] [irc_port]    (Register an IRC server to the known server list)
!irc rmserver <server_name>    (Remove an IRC server from the known server list (Caution: this will remove all connected bridges also))
!irc startserver <server_name>    (Connect the specified server thread to the IRC server)
!irc stopserver <server_name>    (Disconnect the specified server from IRC (and all connected bridges))
!irc addirc <server_name> <bridge_name> <irc_channel>    (Add an IRC bridge to the current channel)
!irc rmirc <server_name> <bridge_name>    (Remove an IRC bridge from slack)
!irc startirc <server_name> <bridge_name>    (Connect a registered IRC bridge)
!irc stopirc <server_name> <bridge_name>    (Disconnect a registered IRC bridge)
!irc ircstatus    (Shows a list of currently registered irc bridges)
```

## Usage for irc bridges

The irc handler supports bridges for multiple irc servers and channels. When an irc bridge is started, it will read
from the irc channel and post the messages to the slack channel, in which it was created.

1. Edit irc_config.json to change the behaviour of the irc bridges

use_message_queue : Enable message queuing for pushing messages to slack to avoid hitting the slack api rate limit.
message_queue_interval : Interval, in which messages from the queue will be posted to the slack server
irc_process_interval : Update interval, in which irc messages will be read

2. Register irc servers and bridges

Before a bridge can be used, the corresponding server must be registered and the bridge must be added to that server.

!addserver freenode irc.freenode.org
!addirc freenode ctfbridge ctfchannel

The bot will remember the servers and bridges until you remove them explicitly.

!rmirc freenode ctfbridge
!rmserver freenode

To activate an irc bridge, the server must be connected first.

!startserver freenode
!startirc freenode ctfbridge (start when server finished connecting.)

After this, the bridge will update the slack channel whenever new messages from irc arrives (and the message queue got
triggered).

If the irc channel gets to spammy, every bridge can be disconnected separately.

!stopirc freenode ctfbridge

or a complete irc server can be stopped (which will also leave all irc channels)

!stopserver freenode

## Installation

1. Copy `config.json.template` to `config.json`
2. Fill the API token and bot name in the config.json file.
3. Add your user id (slack id, not the username) to `admin_users` group in `config.json`
4. `docker build -t ota-challenge-bot .`
5. `docker run -it --rm --name live-ota-challenge-bot ota-challenge-bot`


## Development

1. Copy `config.json.template` to `config.json`
2. Fill the API token and bot name in the config.json file.
3. Create a virtual env: `python3 -m venv .venv`
4. Enter the virtual env: `source .venv/bin/activate`
5. Install requirements: `pip install -r requirements.txt`
