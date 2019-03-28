# OTA Challenge Bot

The OTA challenge bot is a helper tool to be used during CTF events
through the Slack platform.

## Features

Main features :
- Tracking CTFs
- Tracking CTF challenges
- Tracking member participation in challenges
- Displaying announcements upon solving a challenge

Secondary features :
- Syscall table for arm, armthumb, x64 and x86

## Usage

```
!ctf addctf <ctf_name>                                          (Adds a new ctf)
!ctf addchallenge <challenge_name> <challenge_category>         (Adds a new challenge for current ctf)
!ctf workon [challenge_name]                                    (Show that you're working on a challenge)
!ctf status                                                     (Show the status for all ongoing ctf's)
!ctf solve [challenge_name] [support_member]                    (Mark a challenge as solved)
!ctf renamechallenge <old_challenge_name> <new_challenge_name>  (Renames a challenge)
!ctf renamectf <old_ctf_name> <new_ctf_name>                    (Renames a ctf)
!ctf reload                                                     (Reload ctf information from slack)
!ctf archivectf                                                 (Archive the challenges of a ctf)
!ctf addcreds <ctf_user> <ctf_pw> [ctf_url]                     (Add credentials for current ctf)
!ctf showcreds                                                  (Show credentials for current ctf)
!ctf postsolves <title>                                         (Post current solve status to git)
!ctf unsolve [challenge_name]                                   (Remove solve of a challenge)

!syscalls available                                             (Shows the available syscall architectures)
!syscalls show <arch> <syscall name/syscall id>                 (Show information for a specific syscall)

!bot ping                                                       (Ping the bot)
!bot intro                                                      (Show an introduction message for new members)
!bot version                                                    (Show git information about the running version of the bot)

!admin show_admins                                              (Show a list of current admin users)
!admin add_admin <user_id>                                      (Add a user to the admin user group)
!admin remove_admin <user_id>                                   (Remove a user from the admin user group)
!admin as <@user> <command>                                     (Execute a command as another user)

!wolfram ask <question>                                         (Ask wolfram alpha a question)
```

## Retrieving the API token

Bot applications are not allowed to access all api methods from Slack. Thus, if
you create a bot integration on slack, the bot won't be able to create new
channels for example. To get around this restriction, you have to create a real
slack user and generate an authentication token for it, which can then be used
instead of a bot token.

1. Create a new user in slack (this will be the bot user, so give it an appropriate username)
2. Log into slack with this newly created user
3. Navigate to https://api.slack.com/custom-integrations/legacy-tokens
  * The user should show up there together with your slack workspace
5. Press "Create token"
  * This should create a token starting with "xoxp-"
7. Use this token as the `api_key` for the bot
8. Logout and login with your regular user again.

After restarting the bot, the bot user should now show up in your slack workspace.


## Installation

1. Copy `config.json.template` to `config.json`
2. Fill the API token and bot name in the config.json file.
3. Add your user id (slack id, not the username) to `admin_users` group in `config.json`
4. If you want to use the wolfram alpha api, register a valid app id on http://products.wolframalpha.com/api/ and set `wolfram_app_id` in `config.json`
5. Copy `intro_msg.template` to `intro_msg` and set a proper introduction message, which can be shown with `!intro`
6. `docker build -t ota-challenge-bot .`
7. `docker run -it --rm --name live-ota-challenge-bot ota-challenge-bot`


## Development

1. Copy `config.json.template` to `config.json`
2. Fill the API token and bot name in the config.json file.
3. Create a virtual env: `python3 -m venv .venv`
4. Enter the virtual env: `source .venv/bin/activate`
5. Install requirements: `pip install -r requirements.txt`


## Using git support for uploading solve updates

1. Copy `config_solvetracker.json.template` to `config_solvetracker.json`.
2. Configure the git account, the local repo and the remote path, which should be used to access your git repository.

Example:
```
{
    "git_repopath" : "/home/ota_bot/OTA_Upload",
    "git_repouser" : "otabot",
    "git_repopass" : "password",
    "git_remoteuri" : "github.com/ota_bot/OTA_Upload.git",
    "git_branch" : "master",
    "git_baseurl" : "https://ota.github.io/SolveTracker"
}
```

3. Update the templates in `templates` according to your preferences (or go with the default ones).
4. Make sure that there's a `_posts` and `_stats` folder in your git repository.
4. You should be good to go now and git support should be active on the next startup. You can now use the `postsolves` command to push blog posts with the current solve status to git.


## Using Link saver

1. Setup a github repo with jekyll and staticman (e.g. https://github.com/ujjwal96/links).
2. Copy `config_savelink.json.template` to `config_savelink.json`.
3. Configure the git repo and branch to be used.
4. Add the decrypted staticman-token used in `staticman.yml` in the config.
