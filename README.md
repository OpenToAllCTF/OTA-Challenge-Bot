# OTA Challenge Bot

The OTA challenge bot is a helper tool to be used during CTF events
through the Slack platform.

## Features

Main features :
- Tracking CTFs
- Tracking CTF challenges
- Tracking member participation in challenges
- Annoucements upon solving a challenge

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
