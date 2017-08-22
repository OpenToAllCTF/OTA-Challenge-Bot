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

  def __init__(self, args, user):
    if len(args) < 1:
      raise InvalidCommand("Usage : add ctf <ctf_name>")

    self.name = args[0]
    self.user = user

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
    invite_user(slack_client, self.user, channel)

    # New CTF object
    ctf = CTF(channel, self.name)

    # Update list of CTFs
    ctfs = pickle.load(open(ChallengeHandler.DB, "rb"))
    ctfs.append(ctf)
    pickle.dump(ctfs, open(ChallengeHandler.DB, "wb"))

class AddChallengeCommand(Command):
  """
    Add and keep track of a new challenge for a given CTF
  """

  def __init__(self, args, channel_id, user):
    if len(args) < 1:
      raise InvalidCommand("Usage : add challenge <challenge_name>")

    self.name = args[0]
    self.ctf_channel_id = channel_id
    self.user = user

  def execute(self, slack_client):

    # Validate that the user is in a CTF channel
    ctf = is_ctf_channel(ChallengeHandler.DB, self.ctf_channel_id)
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
    invite_user(slack_client, self.user, channel_id)

    # New Challenge object
    challenge = Challenge(channel_id, self.name)

    # Update list of CTFs
    ctfs = pickle.load(open(ChallengeHandler.DB, "rb"))
    ctf = list(filter(lambda x : x.channel_id == ctf.channel_id, ctfs))[0]
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

    response = ""
    for ctf in ctfs:
      response += "*============= %s =============*\n" % ctf.name
      for challenge in ctf.challenges:
        response += "*%s*\n" % challenge.name

    response = response.strip()
    slack_client.api_call("chat.postMessage",
        channel=self.channel, text=response)

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
    ctf = is_ctf_channel(ChallengeHandler.DB, self.ctf_channel_id)
    if not ctf:
      raise InvalidCommand("Command failed. You are not in a CTF channel.")

    # Get channel for challenge name
    channel_info = get_channel_info_from_name(slack_client, self.challenge_name)

    if not channel_info:
      raise InvalidCommand("This challenge does not exist.")

    # Invite user to challenge channel
    invite_user(slack_client, self.user_id, channel_info['id'])

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

  def __init__(self, slack_client):

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
        ctf.add_challenge(challenge)

    # Create the database accordingly
    pickle.dump(database, open(self.DB, "wb+"))
    self.slack_client = slack_client

  def process(self, command, channel, user):
    command_line = unidecode(command.lower())
    args = shlex.split(command_line)
    command = None

    try:
      # Add CTF command
      if args[:2] == ["add", "ctf"]:
        command = AddCTFCommand(args[2:], user)

      # Add challenge command
      elif args[:2] == ["add", "challenge"]:
        command = AddChallengeCommand(args[2:], channel, user)

      # Working command
      elif args[:1] == ["working"]:
        command = WorkingCommand(args[1:], user, channel)

      elif args[:1] == ["status"]:
        command = StatusCommand(channel)

      if command:
        command.execute(self.slack_client)

    except InvalidCommand as e:
      self.slack_client.api_call("chat.postMessage",
        channel=channel, text=e.message)

