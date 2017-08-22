#!/usr/bin/env python3
import json
import pickle

#####
#  SLACK API Wrappers
#####
def invite_user(slack_client, user, channel):
  """
    Invite a user to a given channel
  """
  response = slack_client.api_call("channels.invite",
              channel=channel,
              user=user)
  return response

def set_purpose(slack_client, channel, purpose):
  """
    Set the purpose of a given channel
  """
  response = slack_client.api_call("channels.setPurpose",
    purpose=purpose, channel=channel)

  return response

def create_channel(slack_client, name):
  """
    Create a channel with a given name
  """
  response = slack_client.api_call("channels.create",
      name=name, validate=False)

  return response

def get_channel_info(slack_client, channel_id):
  """
    Get the channel info of a given channel ID
  """
  response = slack_client.api_call("channels.info",
    channel=channel_id)

  return response

def get_channel_info_from_name(slack_client, channel_name):
  response = slack_client.api_call("channels.list")
  for channel in response['channels']:
    purpose = load_json(channel['purpose']['value'])
    if purpose and purpose['name'] == channel_name:
      return channel

  return False

#######
# Helper functions
#######
def load_json(string):
  """
    Return a JSON object based on its string representation.
    Returns false if the string isn't valid JSON.
  """
  try:
    json_object = json.loads(string)
  except ValueError as e:
    return False
  return json_object


#######
# Database manipulation
#######
def is_ctf_channel(database, channel_id):
  """
    Check the database if the channel_id is a CTF channel exists"
    If true, a CTF object is returned.
    Else, the function returns False
  """
  ctfs = pickle.load(open(database, "rb"))
  for ctf in ctfs:
    if ctf.channel_id == channel_id:
      return ctf

  return False

