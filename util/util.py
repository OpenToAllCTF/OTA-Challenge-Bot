import json
import pickle

from util.loghandler import *

#####
#    SLACK API Wrappers
#####

def invite_user(slack_client, user, channel):
    """
    Invite a user to a given channel.
    """
    response = slack_client.api_call("channels.invite",
                                     channel=channel,
                                     user=user)
    return response


def kick_user(slack_client, user_id, channel_id):
    response = slack_client.api_call("channels.kick",
                                     channel=channel_id,
                                     user=user_id)
    return response


def set_purpose(slack_client, channel, purpose):
    """
    Set the purpose of a given channel.
    """
    response = slack_client.api_call("channels.setPurpose",
                                     purpose=purpose, channel=channel)

    return response


def get_members(slack_client):
    """
    Return a list of all members.
    """
    response = slack_client.api_call("users.list", presence=True)
    if not response["ok"]:
        raise Exception("API error")
    return response["members"]


def get_member(slack_client, user_id):
    """
    Return a member for a given user_id.
    """

    response = slack_client.api_call("users.info", user=user_id)
    return response


def get_member_by_name(slack_client, user_name):
    """
    Return the member matching the given user_name.
    """

    memberList = slack_client.api_call("users.list")

    if memberList and memberList['members']:
        for member in memberList['members']:
            if member['name'] == user_name:
                return member

    return None


def create_channel(slack_client, name):
    """
    Create a channel with a given name.
    """

    response = slack_client.api_call("channels.create",
                                     name=name, validate=False)

    return response


def rename_channel(slack_client, channel_id, new_name):
    """
    Rename an existing channel.
    """

    log.debug("Renaming channel {} to {}".format(channel_id, new_name))

    response = slack_client.api_call("channels.rename",
                                     channel=channel_id, name=new_name, validate=False)

    return response


def get_channel_info(slack_client, channel_id):
    """
    Return the channel info of a given channel ID.
    """
    response = slack_client.api_call("channels.info",
                                     channel=channel_id)

    return response


def update_channel_purpose_name(slack_client, channel_id, new_name):
    # Update channel purpose
    channel_info = get_channel_info(slack_client, channel_id)

    if channel_info:
        purpose = load_json(channel_info['channel']['purpose']['value'])
        purpose['name'] = new_name

        set_purpose(slack_client, channel_id, json.dumps(purpose))


#######
# Helper functions
#######
def load_json(string):
    """
    Return a JSON object based on its string representation.
    Return None if the string isn't valid JSON.
    """
    try:
        json_object = json.loads(string)
    except ValueError as e:
        return None
    return json_object

def transliterate(string):
    """
        Converts ascii characters to a unicode
        equivalent.
    """
    mapping = {
        "a" : "ɑ", # \xc9\x91
        "A" : "А", # \xd0\x90
        "e" : "е", # \xd0\xb5
        "E" : "Е", # \xd0\x95
        "i" : "і", # \xd1\x96
        "I" : "І", # \xd0\x86
        "o" : "о", # \xd0\xbe
        "O" : "О", # \xd0\x9e
        "u" : "υ", # \xcf\x85
        "U" : "υ", # \xcf\x85
    }

    return ''.join([mapping[c] if c in mapping else c for c in string])


#######
# Database manipulation
#######
def get_ctf_by_channel_id(database, channel_id):
    """
    Fetch a CTF object in the database with a given channel ID.
    Return the matching CTF object if found, or None otherwise.
    """
    ctfs = pickle.load(open(database, "rb"))
    for ctf in ctfs:
        if ctf.channel_id == channel_id:
            return ctf
        for challenge in ctf.challenges:
            if challenge.channel_id == channel_id:
                return ctf

    return None


def get_ctf_by_name(database, name):
    """
    Fetch a CTF object in the database with a given name.
    Return the matching CTF object if found, or None otherwise.
    """
    ctfs = pickle.load(open(database, "rb"))
    for ctf in ctfs:
        if ctf.name == name:
            return ctf

    return None


def get_challenge_by_name(database, challenge_name, ctf_channel_id):
    """
    Fetch a Challenge object in the database with a given name and ctf channel
    ID.
    Return the matching Challenge object if found, or None otherwise.
    """
    ctfs = pickle.load(open(database, "rb"))
    for ctf in ctfs:
        if ctf.channel_id == ctf_channel_id:
            for challenge in ctf.challenges:
                if challenge.name == challenge_name:
                    return challenge

    return None


def get_challenge_by_channel_id(database, challenge_channel_id):
    """
    Fetch a Challenge object in the database with a given channel ID
    Return the matching Challenge object if found, or None otherwise.
    """
    ctfs = pickle.load(open(database, "rb"))
    for ctf in ctfs:
        for challenge in ctf.challenges:
            if challenge.channel_id == challenge_channel_id:
                return challenge

    return None


def get_challenges_for_user_id(database, user_id, ctf_channel_id):
    """
    Fetch a list of all challenges a user is working on for a given CTF.
    Return a list of matching Challenge objects.
    This should technically only return 0 or 1 challenge, as a user
    can only work on 1 challenge at a time.
    """

    ctfs = pickle.load(open(database, "rb"))
    ctf = list(filter(lambda ctf: ctf.channel_id == ctf_channel_id, ctfs))[0]

    challenges = []
    for challenge in ctf.challenges:
        if player.user_id in challenge.players:
            challenges.append(challenge)

    return challenges


def update_challenge_name(database, challenge_channel_id, new_name):
    """
    Updates the name of the challenge with the specified challenge id
    """
    ctfs = pickle.load(open(database, "rb"))

    for ctf in ctfs:
        for chal in ctf.challenges:
            if chal.channel_id == challenge_channel_id:
                chal.name = new_name
                pickle.dump(ctfs, open(database, "wb"))
                return


def update_ctf_name(database, ctf_channel_id, new_name):
    """
    Updates the name of the ctf with the specified channel id
    """
    ctfs = pickle.load(open(database, "rb"))

    for ctf in ctfs:
        if ctf.channel_id == ctf_channel_id:
            ctf.name = new_name
            pickle.dump(ctfs, open(database, "wb"))
            return
