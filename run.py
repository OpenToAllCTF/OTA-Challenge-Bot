#!/usr/bin/env python3

from slackclient import SlackClient
import json
import time
from handlers import *

def parse_slack_output(slack_rtm_output):
  """
      The Slack Real Time Messaging API is an events firehose.
      this parsing function returns None unless a message is
      directed at the Bot, based on its ID.
  """
  output_list = slack_rtm_output
  if output_list and len(output_list) > 0:
      for output in output_list:
          if output and 'text' in output and AT_BOT in output['text']:
              # return text after the @ mention, whitespace removed
              return (output['text'].split(AT_BOT)[1].strip().lower(),
                     output['channel'],
                     output['user'])
  return None, None, None

def get_bot_id(name):
  """
      Get the slack user ID of the bot
  """
  api_call = slack_client.api_call("users.list")
  if api_call.get('ok'):

      # Retrieve all users so we can find our bot
      users = api_call.get('members')
      for user in users:
          if 'name' in user and user.get('name') == name:
              return user.get('id')
  else:
      print("could not find bot user with the name " + name)

if __name__ == "__main__":

  # Load config file
  with open("./config.json") as f:
    config = json.load(f)

  # Create slack client
  slack_client = SlackClient(config['api_key'])

  # Bot name, ID and AT_BOT
  BOT_NAME = config['bot_name']
  BOT_ID = get_bot_id(BOT_NAME)
  AT_BOT = "<@" + BOT_ID + ">"

  # 1 second delay between reading from firehose
  READ_WEBSOCKET_DELAY = 1

  # Connect to Slack's real-time messaging API
  handlers = [
    challenge_handler.ChallengeHandler(slack_client)
  ]

  if slack_client.rtm_connect():
      print("StarterBot connected and running!")

      # Main loop
      while True:
          command, channel, user = parse_slack_output(slack_client.rtm_read())
          if command and channel:
            [handler.process(command, channel, user) for handler in handlers]

          time.sleep(READ_WEBSOCKET_DELAY)
  else:
      print("Connection failed. Invalid Slack token or bot ID?")
