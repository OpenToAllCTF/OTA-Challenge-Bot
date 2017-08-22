#!/usr/bin/env python3

import shlex
from helpers.command import *
from helpers.invalid_command import *
from unidecode import unidecode

class AddCTFCommand(Command):
  """
    Add and keep track of a new CTF
  """

  def __init__(self, args):
    if len(args) < 1:
      raise InvalidCommand("Usage : add ctf <ctf_name>")

    self.channel = args[0]

  def execute(self, slack_client):
    response = (slack_client.api_call("channels.create",
        name=self.channel, validate=False))

    if response['ok'] == False:
      raise InvalidCommand("\"%s\" channel creation failed.\nError : %s" % (self.channel, response['error']))

class AddChallengeCommand(Command):
  """
    Add and keep track of a new challenge for a given CTF
  """

  def __init__(self, args):
    if len(args) < 2:
      raise InvalidCommand("Usage : add challenge <challenge_name> <ctf_name>")

    self.challenge = args[0]
    self.ctf = args[1]
    self.channel = "%s-%s" % (self.ctf, self.challenge)

  def execute(self, slack_client):
    response = slack_client.api_call("channels.create",
        name=self.channel, validate=False)

    if response['ok'] == False:
      raise InvalidCommand("\"%s\" channel creation failed.\nError : %s" % (self.channel, response['error']))

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
  """

  def __init__(self, slack_client):
   self.slack_client = slack_client

  def process(self, command, channel):
    command_line = unidecode(command.lower())
    args = shlex.split(command_line)
    command = None

    try:
      # Add CTF command
      if args[:2] == ["add", "ctf"]:
        command = AddCTFCommand(args[2:])

      # Add challenge command
      elif args[:2] == ["add", "challenge"]:
        command = AddChallengeCommand(args[2:])

      # Working command
      elif args[:1] == ["working"]:
        command = WorkingCommand(args[1:])

      if command:
        command.execute(self.slack_client)

    except InvalidCommand as e:
      self.slack_client.api_call("chat.postMessage",
        channel=channel, text=e.message)

