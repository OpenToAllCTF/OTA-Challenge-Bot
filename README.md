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
!ctf working [challenge_name]
!ctf status
!ctf solved [challenge_name] [support_member]
```
```
!syscalls available
!syscalls show <arch> <syscall name/syscall id>
```
```
!bot ping
```

## Installation

1. Copy `config.json.template` to `config.json`
2. Fill the API token and bot name in the config.json file.
3. `docker build -t ota-challenge-bot .`
4. `docker run -it --rm --name live-ota-challenge-bot ota-challenge-bot`
