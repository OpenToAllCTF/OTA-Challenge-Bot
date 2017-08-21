#!/usr/bin/env python3

import shlex
from helpers.command import *
from helpers.invalid_command import *

class AddCTFCommand(Command):
  """
    Add and keep track of a new CTF
  """

  def __init__(self, *args):
    self.channel = args[0]

  def execute(self, slack_client):
    print(slack_client.api_call("channels.create",
        name=self.channel, validate=False))

class AddChallengeCommand(Command):
  """
    Add and keep track of a new challenge for a given CTF
  """

  def __init__(self, *args): pass
  def execute(self, slack_client): pass

class ChallengeHandler:
  """
    Manages everything related to challenge coordination.

    Commands :
    # Create a defcon-25-quals channel
    @ota_bot add ctf "defcon 25 quals"

    # Create a web-100 channel
    @ota_bot add challenge "web 100" to "defcon 25 quals"

    # Kick member from other ctf challenge channels and invite the member to the web 100 channel
    @ota_bot working "web 100"
  """

  def __init__(self, slack_client):
   self.slack_client = slack_client

  def process(self, command, channel):
    args = shlex.split(command.lower())

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

    except InvalidCommand as e:
      self.slack_client.api_call("chat.postMessage",
        channel=channel, text=e.message,
        as_user=True)

    if command:
      command.execute(self.slack_client)
