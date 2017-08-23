# OTA Challenge Bot

The OTA challenge bot is a helper tool to be used during CTF events.

## Features
The bot allows members to :
 - Keep track of which challenges other members are working on
 - Keep track of solved/unsolved challenges

When members begin working on new challenges, the OTA bot will
automatically create a slack channel for a given challenge, as well
as invite players to the relevant channel.

Other interesting features include :
 - Creating an IRC bridge for a given CTF
 - Automatic @channel notifications before a CTF begins and ends.

## Usage

```
# Create a defcon-25-quals channel
@ota_bot add ctf "defcon 25 quals"

# Create a defcon-25-quals-web-100 channel (the ctf name is prepended based on the channel where you run the command)
@ota_bot add challenge "web 100"

# Invite the member to the web 100 channel
@ota_bot working "web 100"

# Set a challenge as solved and notify the channel.
@ota_bot solved "web 100"

# Unsolve a challenge and notify the channel
@ota_bot unsolve "web 100"

# View status of members/solves
@ota_bot status

# Add IRC bridge channel "defcon-25-quals-irc"
@ota_bot add irc "#defcon-quals" to "defcon 25 quals"
```

The status response looks like the following :
```
ota_bot :
=== Defcon 25 Quals ===
web 100 (4) => Lyla, Edward, Eric, Theodore
pwn 200 (0)
pwn 400 (1) => 3p1c_h4x0r

=== OTA CTF 2017 ===
web 100 (1) => Johnny
rev 200 (0)
```

Notifications :
```
ota_bot: Defcon 25 Quals ends in 2 hours!
```

## Installation

1. Copy `config.json.template` to `config.json`
2. Fill the APi token and bot name in the config file.
3. `docker build -t ota-challenge-bot .`
4. `docker run -it --rm --name live-ota-challenge-bot ota-challenge-bot`
