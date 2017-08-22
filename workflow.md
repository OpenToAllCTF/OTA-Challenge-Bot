# CTF Team Workflow

The goal of the OTA bot is to coordinate team members in solving CTF challenges efficiently
through Slack. For this bot to work as intended, I suggest reading the following guide on how the OTA bot operates
during CTFs.

### Bot Usage
Here is a summary of the general commands members can use during a CTF.

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

### General Flow

1. When preparing for a new CTF, use the command `@ota_bot add ctf <ctf_name>`.
This will create a dedicated Slack channel for the event. Members who wish to participate
in the competition will then join the CTF channel manually.

2. When the competition begins, a number of challenges will be available. Use the
`@ota_bot add challenge <challenge_name>` command to keep track of currently available
challenges. This will create a new dedicated channel for that CTF challenge.

3. **When you'll want to work on a challenge, use the `@ota_bot working <challenge_name>`.
This will assign your username to the challenge, allowing other players to see who's working
on what. This is your most important command. Use it often :)**

4. When you solve a challenge, use the `@ota_bot solved <challenge_name>` command. Using
this command will notify people of the challenge you just solved.

5. Throughout the CTF, it's a good idea to view who's working on which challenge in order
to balance the workload equally. Use the `@ota_bot status` command to get an overview
of what's solved and who's working on what.
