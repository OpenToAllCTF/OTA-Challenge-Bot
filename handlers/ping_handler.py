#!/usr/bin/env python3

import shlex
import pickle
import re
import json
from unidecode import unidecode
from helpers.command import *


class PingCommand(Command):
  """
    Ping this server to check for uptime
  """
  def __init__(self, channel_id):
    self.channel_id = channel_id

  def execute(self, slack_client):

    # Announce the CTF channel
    message = "Pong!"

    slack_client.api_call("chat.postMessage",
      channel=self.channel_id, text=message, as_user=True)

class PingHandler:
  """
    Ping this server to check for uptime
  """

  def __init__(self, slack_client):
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

    # Add CTF command
    if args[:1] == ["ping"]:
      command = PingCommand(channel)

    if command:
      command.execute(self.slack_client)
