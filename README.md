# OTA Challenge Bot

[![CircleCI (development)](https://circleci.com/gh/OpenToAllCTF/OTA-Challenge-Bot/tree/development.svg?style=svg)](https://circleci.com/gh/OpenToAllCTF/OTA-Challenge-Bot/tree/development)

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
!ctf tag [<challenge_name>] <tag> [..<tag>]                     (Adds a tag to a challenge)
!ctf workon [challenge_name]                                    (Show that you're working on a challenge)
!ctf status                                                     (Show the status for all ongoing ctf's)
!ctf solve [challenge_name] [support_member]                    (Mark a challenge as solved)
!ctf renamechallenge <old_challenge_name> <new_challenge_name>  (Renames a challenge)
!ctf renamectf <old_ctf_name> <new_ctf_name>                    (Renames a ctf)
!ctf reload                                                     (Reload ctf information from slack)
!ctf removetag [<challenge_name] <tag> [..<tag>]                (Remove a tag from a challenge)
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

## Retrieving the API tokens

Bot applications are not allowed to access all api methods from Slack. Thus, if
you create a bot integration on slack, the bot won't be able to create new
channels for example. To get around this restriction you must create a new
slack integration ("Slack App"), assign it to your workspace, enable the Socket
Mode event feed, generate an "App Level Token" (`xapp1`), assign scopes to your
bot user and subsequently create a "Bot User Token" (`xoxb`), and then finally
install it to your workspace. 

Once generated, the tokens must be scoped to the appropriate privilege levels
required for the bot to function. Finally, you must ensure that you have
subscribed the bot users to the list of events it will need to receive in order
to operate.

1. First, navigate to `api.slack.com/apps` and create a new slack app. Give it
a name and select the workspace that it will serve, and then click create.

2. Enable socket mode by clicking on the menu of the same name and then
clicking on the toggle labelled "Enable Socket Mode". You'll be prompted to
create an App Level Token which you must do next.

3. App Level Token

This token is used by the bot to access the websocket event feed in version 3
of the Slack API. The toggle you enabled in the previous step, "Enable Socket
Mode", is what turns on the event feed. Assuming you've not already created an
App Level Token you'll now be prompted to do so. Place it into the config file
under the entry `app_key`.

4. Bot User Token

This token is used by the bot to interact with the workspace and users via
Slack's conversations API. In order to create this token you must first
navigate to the OAuth & Permissions section of the Slack API control panel.

Once there, take note of the greyed out "Install to Workspace" button. You need
to add scopes to the bot user's token before you can install the bot. Scroll
down to the bottom of this page and in the section labelled "Bot Token Scopes"
add the following scopes.

```
app_mentions:read
channels:history
channels:join
channels:manage
channels:read
chat:write
chat:write.customize
chat:write.public
dnd:read
groups:history
groups:read
groups:write
im:history
im:read
im:write
links:read
links:write
mpim:history
mpim:read
mpim:write
reactions:read
reactions:write
reminders:list
reminders:write
team:read
users:read
users:write
```

Next, return to the top of the page and install the bot user using the button
from before which should no longer be greyed out. Now copy the "Bot User OAuth
Access Token" (begins with `xoxb`) into the config file under the entry
`api_key`. The bot should show up inside the workspace now. You can change its
display name using the menu on the left labelled "Basic Information", if you
want.

5. Event subscription

NOTE: Make sure you toggle "Enable Socket" (step 2) before attempting this!

Once the tokens have been configured you will need to navigate to the Event
Subscriptions panel of the slack API control panel and register the bot to
receive the events it needs to operate. 

First toggle the switch labelled "Enable Events", then use the picker to select
at least the events below. They are probably all that you will need, but it's
fine to select all of the event subscriptions here if you want to be on the simple side. 

```
app_mention
app_mentions:read
channels:history
emoji_changed
emoji:read
groups:history
im:history
link_shared
links:read
message.channels
message.im
message.groups
message.mpim
mpim:history
reaction_added
reactions:read
reaction_removed
```


## Installation

1. Copy _config/config.json.template_ to _config/config.json_
2. Fill the APP and API token names in the _config.json_ file.
3. Add your user id (slack id, not the username) to `admin_users` group in _config/config.json_
4. If you want to use the wolfram alpha api, register a valid app id on http://products.wolframalpha.com/api/ and set `wolfram_app_id` in `config/config.json`
5. Copy _intro_msg.template_ to _intro_msg_ and set a proper introduction message, which can be shown with `!intro`
6. `docker build -t ota-challenge-bot .`
7. `docker run -it --rm --name live-ota-challenge-bot ota-challenge-bot`


## Development

1. Copy _config/config.json.template_ to _config/config.json_
2. Fill the API token and bot name in the _config.json_ file.
3. Create a virtual env: `python3 -m venv .venv`
4. Enter the virtual env: `source .venv/bin/activate`
5. Install requirements: `pip install -r requirements.txt`


## Using git support for uploading solve updates

1. Copy _config/config_solvetracker.json.template_ to _config/config_solvetracker.json_.
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

Alternatively, you may decide to omit the `git_repopass` entry. In such an event (or if the entry is left blank) then the handler will attempt to push to the configured "git_remoteuri" using the `git` protocol, including using any SSH identities you may have configured.
Note: If you configure the solvetracker this way, you need to make sure you are using an SSH identity without a passphrase.

3. Update the templates in `templates` according to your preferences (or go with the default ones).
4. Make sure that there's a __posts_ and __stats_ folder in your git repository.
5. You should be good to go now and git support should be active on the next startup. You can now use the `postsolves` command to push blog posts with the current solve status to git.


## Using Link saver

1. Setup a github repo with jekyll and staticman (e.g. https://github.com/ujjwal96/links).
2. Copy _config/config_savelink.json.template_ to _config/config_savelink.json_.
3. Configure the git repo and branch to be used.
4. Add the decrypted staticman-token used in _staticman.yml_ in the config.
5. Add a link to your repo, so people can look it up via `showlinkurl`

Example:
```
{
    "git_repo": "reponame/links",
    "git_branch": "gh-pages",
    "staticman-token": "9d837771-945a-489d-cd80-13abcdefa112",
    "allowed_users": [],
    "repo_link_url": "https://reponame.github.io/links/"
}
```

## Archive reminder

To enable archive reminders set an offset (in hours) in _config/config.json_ for `archive_ctf_reminder_offset`. Clear or remove the setting to disable reminder handling.

If active, the bot will create a reminder for every bot admin on `!endctf` to inform him, when the ctf was finished for the specified time and it should be archived.

Example (for being reminded one week after the ctf has finished):
```
{
    ...
    "archive_ctf_reminder_offset" : "168"
}
```

## Log command deletion

To enable logging of deleting messages containing specific keywords, set `delete_watch_keywords` in _config/config.json_ to a comma separated list of keywords. 
Clear or remove the setting to disable deletion logging.

Example
```
{
    "delete_watch_keywords" : "workon, reload, endctf"
}
