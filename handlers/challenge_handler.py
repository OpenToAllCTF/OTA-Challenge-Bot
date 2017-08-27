#!/usr/bin/env python3
import pickle
import re
from bottypes.ctf import *
from bottypes.challenge import *
from bottypes.player import *
from handlers.handler_factory import *
from handlers.base_handler import *
from util.util import *

class AddCTFCommand(Command):
  """
    Add and keep track of a new CTF.
  """    
  def execute(self, slack_client, args, user_id, channel_id):
    if len(args) < 1:
      raise InvalidCommand("Usage: `!ctf addctf <ctf_name>`")

    name = args[0]
    
    # Create the channel
    response = create_channel(slack_client, name)

    # Validate that the channel was successfully created.
    if response['ok'] == False:
      raise InvalidCommand("\"%s\" channel creation failed.\nError : %s" % (name, response['error']))

    # Add purpose tag for persistence
    purpose = dict(ChallengeHandler.CTF_PURPOSE)
    purpose['name'] = name
    purpose = json.dumps(purpose)
    channel = response['channel']['id']
    set_purpose(slack_client, channel, purpose)

    # Invite user
    invite_user(slack_client, user_id, channel)

    # New CTF object
    ctf = CTF(channel, name)

    # Update list of CTFs
    ctfs = pickle.load(open(ChallengeHandler.DB, "rb"))
    ctfs.append(ctf)
    pickle.dump(ctfs, open(ChallengeHandler.DB, "wb"))

    # Notify people of new channel
    message = "Created channel #%s" % response['channel']['name']
    slack_client.api_call("chat.postMessage", channel=channel_id, text=message.strip(), as_user=True, parse="full")

class AddChallengeCommand(Command):
  """
    Add and keep track of a new challenge for a given CTF
  """
  def execute(self, slack_client, args, channel_id, user_id):
    if len(args) < 1:
      raise InvalidCommand("Usage: `!ctf addchallenge <challenge_name>`")
    name = args[0]

    # Validate that the user is in a CTF channel
    ctf = get_ctf_by_channel_id(ChallengeHandler.DB, channel_id)

    if not ctf:
      raise InvalidCommand("Command failed. You are not in a CTF channel.")

    # Create the challenge channel
    channel_name = "%s-%s" % (ctf.name, name)
    response = create_channel(slack_client, channel_name)

    # Validate that the channel was created successfully
    if not response['ok']:
      raise InvalidCommand("\"%s\" channel creation failed.\nError : %s" % (channel_name, response['error']))

    # Add purpose tag for persistence
    challenge_channel_id = response['channel']['id']
    purpose = dict(ChallengeHandler.CHALL_PURPOSE)
    purpose['name'] = name
    purpose['ctf_id'] = ctf.channel_id
    purpose = json.dumps(purpose)
    set_purpose(slack_client, challenge_channel_id, purpose)

    # Invite user
    invite_user(slack_client, user_id, challenge_channel_id)

    # New Challenge and player object
    challenge = Challenge(challenge_channel_id, name)
    player = Player(user_id)

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

  def execute(self, slack_client, args, channel_id, user_id):
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
        channel=channel_id, text=response.strip(), as_user=True)

class WorkingCommand(Command):
  """
    Mark a player as "working" on a challenge.
  """

  def execute(self, slack_client, args, channel_id, user_id):
    if len(args) < 1:
      raise InvalidCommand("Usage: `working <challenge_name>`")
    challenge_name = args[0]

    # Validate that current channel is a CTF channel
    ctf = get_ctf_by_channel_id(ChallengeHandler.DB, channel_id)

    if not ctf:
      raise InvalidCommand("Command failed. You are not in a CTF channel.")

    # Get challenge object for challenge name
    challenge = get_challenge_by_name(ChallengeHandler.DB, challenge_name, ctf.channel_id)

    if not challenge:
      raise InvalidCommand("This challenge does not exist.")

    # Invite user to challenge channel
    invite_user(slack_client, user_id, challenge.channel_id)

    # Update database
    ctfs = pickle.load(open(ChallengeHandler.DB, "rb"))
    ctf = list(filter(lambda x : x.channel_id == ctf.channel_id, ctfs))[0]
    for c in ctf.challenges:
      if c.channel_id == challenge.channel_id:
        c.add_player(Player(user_id))
    pickle.dump(ctfs, open(ChallengeHandler.DB, "wb"))

class SolveCommand(Command):
  """
    Mark a challenge as solved.
  """

  def execute(self, slack_client, args, channel_id, user_id):
    if len(args) < 1:
      raise InvalidCommand("Usage: `!ctf solved <challenge_name>`")

    challenge_name = args[0]
    
    challenge = get_challenge_by_name(ChallengeHandler.DB, challenge_name, channel_id)

    if not challenge:
      raise InvalidCommand("This challenge does not exist.")

    # Update database
    ctfs = pickle.load(open(ChallengeHandler.DB, "rb"))
    ctf = list(filter(lambda x : x.channel_id == channel_id, ctfs))[0]
    challenge = list(filter(lambda x : x.channel_id == challenge.channel_id, ctf.challenges))[0]
    challenge.mark_as_solved(user_id)
    pickle.dump(ctfs, open(ChallengeHandler.DB, "wb"))

    # Announce the CTF channel
    member = get_member(slack_client, user_id)
    message = "<@here> *%s* : %s has solved the \"%s\" challenge" % (challenge.name, member['user']['name'], challenge.name)
    message += "."

    slack_client.api_call("chat.postMessage", channel=channel_id, text=message, as_user=True)

class HelpCommand(Command):
    """
      Displays a help menu
    """

    def execute(self, slack_client, args, channel_id, user_id):      
      message = "```"
      message += "!ctf addctf <ctf_name>\n"
      message += "!ctf addchallenge <challenge_name>\n"
      message += "!ctf working <challenge_name>\n"
      message += "!ctf solved <challenge_name>\n"
      message += "!ctf status\n"
      message += "```"

      raise InvalidCommand(message)

class ChallengeHandler(BaseHandler):
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
  
  def __init__(self):    
    self.commands = {
      "addctf" : AddCTFCommand,
      "addchallenge" : AddChallengeCommand,
      "working" : WorkingCommand,
      "status" : StatusCommand,
      "solved" : SolveCommand,
      "help" : HelpCommand
    }  

  """
  This might be refactored. Not sure, if the handler itself should do the channel handling,
  or if it should be used to a common class, so it can be reused
  """
  def init(self, slack_client, bot_id):
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
        l = list(filter(lambda ctf : ctf.channel_id == ctf_channel_id, database))
        ctf = l[0] if l else None
        if ctf:
          for member_id in channel['members']:
            if member_id != bot_id:
              challenge.add_player(Player(member_id))
          ctf.add_challenge(challenge)

    # Create the database accordingly
    pickle.dump(database, open(self.DB, "wb+"))    

# Register this handler
HandlerFactory.registerHandler("ctf", ChallengeHandler())