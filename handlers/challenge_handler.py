#!/usr/bin/env python3

import shlex
import pickle
import re
import json
from helpers.command import *
from helpers.invalid_command import *
from helpers.ctf import *
from helpers.challenge import *
from helpers.player import *
from helpers.util import *
from unidecode import unidecode

class AddCTFCommand(Command):
  """
    Add and keep track of a new CTF.
  """

  def __init__(self, args, user, channel):
    if len(args) < 1:
      raise InvalidCommand("Usage : add ctf <ctf_name>")

    self.name = args[0]
    self.user_id = user
    self.channel_id = channel

  def execute(self, slack_client):

    # Create the channel
    response = create_channel(slack_client, self.name)

    # Validate that the channel was successfully created.
    if response['ok'] == False:
      raise InvalidCommand("\"%s\" channel creation failed.\nError : %s" % (self.name, response['error']))

    # Add purpose tag for persistence
    purpose = dict(ChallengeHandler.CTF_PURPOSE)
    purpose['name'] = self.name
    purpose = json.dumps(purpose)
    channel = response['channel']['id']
    set_purpose(slack_client, channel, purpose)

    # Invite user
    invite_user(slack_client, self.user_id, channel)

    # New CTF object
    ctf = CTF(channel, self.name)

    # Update list of CTFs
    ctfs = pickle.load(open(ChallengeHandler.DB, "rb"))
    ctfs.append(ctf)
    pickle.dump(ctfs, open(ChallengeHandler.DB, "wb"))

    # Notify people of new channel
    message = "Created channel #%s" % response['channel']['name']
    slack_client.api_call("chat.postMessage",
        channel=self.channel_id, text=message.strip(), as_user=True, parse="full")


class AddChallengeCommand(Command):
  """
    Add and keep track of a new challenge for a given CTF
  """

  def __init__(self, args, channel_id, user_id):
    if len(args) < 1:
      raise InvalidCommand("Usage : add challenge <challenge_name>")

    self.name = args[0]
    self.ctf_channel_id = channel_id
    self.user_id = user_id

  def execute(self, slack_client):

    # Validate that the user is in a CTF channel
    ctf = get_ctf_by_channel_id(ChallengeHandler.DB, self.ctf_channel_id)
    if not ctf:
      raise InvalidCommand("Command failed. You are not in a CTF channel.")

    # Create the challenge channel
    channel_name = "%s-%s" % (ctf.name, self.name)
    response = create_channel(slack_client, channel_name)

    # Validate that the channel was created successfully
    if not response['ok']:
      raise InvalidCommand("\"%s\" channel creation failed.\nError : %s" % (channel_name, response['error']))

    # Add purpose tag for persistence
    channel_id = response['channel']['id']
    purpose = dict(ChallengeHandler.CHALL_PURPOSE)
    purpose['name'] = self.name
    purpose['ctf_id'] = ctf.channel_id
    purpose = json.dumps(purpose)
    set_purpose(slack_client, channel_id, purpose)

    # Invite user
    invite_user(slack_client, self.user_id, channel_id)

    # New Challenge and player object
    challenge = Challenge(channel_id, self.name)
    player = Player(self.user_id)

    # Update database
    ctfs = pickle.load(open(ChallengeHandler.DB, "rb"))
    ctf = list(filter(lambda x : x.channel_id == ctf.channel_id, ctfs))[0]
    challenge.add_player(player)
    ctf.add_challenge(challenge)
    pickle.dump(ctfs, open(ChallengeHandler.DB, "wb"))

class StatusCommand(Command):
  """
    Get a status of the currently running CTFs
  """

  def __init__(self, channel):
    self.channel = channel

  def execute(self, slack_client):
    ctfs = pickle.load(open(ChallengeHandler.DB, "rb"))
    members = get_members(slack_client)['members']
    response = ""
    for ctf in ctfs:
      response += "*============= %s =============*\n" % ctf.name
      for challenge in ctf.challenges:
        response += "*%s* (Total : %d) " % (challenge.name, len(challenge.players))
        players = []
        if not challenge.is_solved:
          response += "Active : "
          for player in challenge.players:
            player_name = list(filter(lambda m: m['id'] == player.user_id and m['presence'] == 'active', members))[0]['name']
            players.append(player_name)
          response += ', '.join(players) + "\n"
        else:
          player_name = list(filter(lambda m: m['id'] == challenge.solver and m['presence'] == 'active', members))[0]['name']
          response += "Solved by %s : :tada:" % player_name
      response += "\n"

    slack_client.api_call("chat.postMessage",
        channel=self.channel, text=response.strip(), as_user=True)

class WorkingCommand(Command):
  """
    Mark a player as "working" on a challenge.
  """

  def __init__(self, args, user_id, ctf_channel_id):

    if len(args) < 1:
      raise InvalidCommand("Usage : working <challenge_name>")

    self.challenge_name = args[0]
    self.user_id = user_id
    self.ctf_channel_id = ctf_channel_id

  def execute(self, slack_client):

    # Validate that current channel is a CTF channel
    ctf = get_ctf_by_channel_id(ChallengeHandler.DB, self.ctf_channel_id)
    if not ctf:
      raise InvalidCommand("Command failed. You are not in a CTF channel.")

    # Get challenge object for challenge name
    challenge = get_challenge_by_name(ChallengeHandler.DB, self.challenge_name, ctf.channel_id)

    if not challenge:
      raise InvalidCommand("This challenge does not exist.")

    # Invite user to challenge channel
    invite_user(slack_client, self.user_id, challenge.channel_id)

    # Update database
    ctfs = pickle.load(open(ChallengeHandler.DB, "rb"))
    ctf = list(filter(lambda x : x.channel_id == ctf.channel_id, ctfs))[0]
    for c in ctf.challenges:
      if c.channel_id == challenge.channel_id:
        c.add_player(Player(self.user_id))
    pickle.dump(ctfs, open(ChallengeHandler.DB, "wb"))

class SolveCommand(Command):
  """
    Mark a challenge as solved.
  """

  def __init__(self, args, ctf_channel_id, user_id):
    if len(args) < 1:
      raise InvalidCommand("Usage : @ota_bot solved <challenge_name>")

    self.user_id = user_id
    self.challenge_name = args[0]
    self.ctf_channel_id = ctf_channel_id

  def execute(self, slack_client):
    challenge = get_challenge_by_name(ChallengeHandler.DB, self.challenge_name, self.ctf_channel_id)

    if not challenge:
      raise InvalidCommand("This challenge does not exist.")

    # Update database
    ctfs = pickle.load(open(ChallengeHandler.DB, "rb"))
    ctf = list(filter(lambda x : x.channel_id == self.ctf_channel_id, ctfs))[0]
    challenge = list(filter(lambda x : x.channel_id == challenge.channel_id, ctf.challenges))[0]
    challenge.mark_as_solved(self.user_id)
    pickle.dump(ctfs, open(ChallengeHandler.DB, "wb"))

    # Announce the CTF channel
    member = get_member(slack_client, self.user_id)
    message = "<@here> *%s* : %s has solved the \"%s\" challenge" % (challenge.name, member['user']['name'], challenge.name)
    message += "."

    slack_client.api_call("chat.postMessage",
      channel=self.ctf_channel_id, text=message, as_user=True)

class HelpCommand(Command):
    """
      Displays a help menu
    """

    def execute(self, slack_client):
      message = "Available Commands : "
      message += "```"
      message += "@ota_bot add ctf <ctf_name>\n"
      message += "@ota_bot add challenge <challenge_name>\n"
      message += "@ota_bot working <challenge_name>\n"
      message += "@ota_bot solved <challenge_name>\n"
      message += "@ota_bot status\n"
      message += "```"

      raise InvalidCommand(message)

class ChallengeHandler:
  """
    Manages everything related to challenge coordination.

    Commands :
    # Create a defcon-25-quals channel
    @ota_bot add ctf "defcon 25 quals"

    # Create a web-100 channel
    @ota_bot add challenge "web 100" "defcon 25 quals"

    # Kick member from other ctf challenge channels and invite the member to the web 100 channel
    @ota_bot working "web 100"

    # Get status of all CTFs
    @ota_bot status
  """

  DB = "databases/challenge_handler.bin"
  CTF_PURPOSE = {
    "ota_bot" : "DO_NOT_DELETE_THIS",
    "name" : "",
    "type" : "CTF"
  }

  CHALL_PURPOSE = {
    "ota_bot" : "DO_NOT_DELETE_THIS",
    "ctf_id" : "",
    "name" : "",
    "type" : "CHALLENGE"
  }

  def __init__(self, slack_client, bot_id):

    # Find channels generated by challenge_handler
    database = []
    response = slack_client.api_call("channels.list")

    # Find active CTF channels
    for channel in response['channels']:
      purpose = load_json(channel['purpose']['value'])

      if not channel['is_archived'] and purpose and "ota_bot" in purpose and purpose["type"] == "CTF":
        ctf = CTF(channel['id'], purpose['name'])
        database.append(ctf)

    # Find active challenge channels
    for channel in response['channels']:
      purpose = load_json(channel['purpose']['value'])

      if not channel['is_archived'] and purpose and "ota_bot" in purpose and purpose["type"] == "CHALLENGE":
        challenge = Challenge(channel['id'], purpose["name"])
        ctf_channel_id = purpose["ctf_id"]
        ctf = list(filter(lambda ctf : ctf.channel_id == ctf_channel_id, database))[0]
        for member_id in channel['members']:
          if member_id != bot_id:
            challenge.add_player(Player(member_id))
        ctf.add_challenge(challenge)

    # Create the database accordingly
    pickle.dump(database, open(self.DB, "wb+"))
    self.slack_client = slack_client

  def process(self, command, channel, user):
    try:
      command_line = unidecode(command.lower())
      args = shlex.split(command_line)
      command = None
    except:
      message = "Command failed : Malformed input."
      self.slack_client.api_call("chat.postMessage",
        channel=channel, text=message, as_user=True)
      return

    try:
      # Add CTF command
      if args[:2] == ["add", "ctf"]:
        command = AddCTFCommand(args[2:], user, channel)

      # Add challenge command
      elif args[:2] == ["add", "challenge"]:
        command = AddChallengeCommand(args[2:], channel, user)

      # Working command
      elif args[:1] == ["working"]:
        command = WorkingCommand(args[1:], user, channel)

      elif args[:1] == ["status"]:
        command = StatusCommand(channel)

      elif args[:1] == ["solved"]:
        command = SolveCommand(args[1:], channel, user)

      else:
        command = HelpCommand()

      if command:
        command.execute(self.slack_client)

    except InvalidCommand as e:
      self.slack_client.api_call("chat.postMessage",
        channel=channel, text=e.message, as_user=True)

