import json
import pickle

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
    return response


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

    print("Creating channel: %s" % name)

    response = slack_client.api_call("channels.create",
            name=name, validate=False)

    return response


def get_channel_info(slack_client, channel_id):
    """
    Return the channel info of a given channel ID.
    """
    response = slack_client.api_call("channels.info",
        channel=channel_id)

    return response


#######
# Helper functions
#######
def load_json(string):
    """
    Return a JSON object based on its string representation.
    Return false if the string isn't valid JSON.
    """
    try:
        json_object = json.loads(string)
    except ValueError as e:
        return False
    return json_object


#######
# Database manipulation
#######
def get_ctf_by_channel_id(database, channel_id):
    """
    Fetch a CTF object in the database with a given channel ID.
    Return the matching CTF object if found, or False otherwise.
    """
    ctfs = pickle.load(open(database, "rb"))
    for ctf in ctfs:
        if ctf.channel_id == channel_id:
            return ctf
        for challenge in ctf.challenges:
            if challenge.channel_id == channel_id:
                return ctf

    return False


def get_challenge_by_name(database, challenge_name, ctf_channel_id):
    """
    Fetch a Challenge object in the database with a given name and ctf channel
    ID.
    Return the matching Challenge object if found, or False otherwise.
    """
    ctfs = pickle.load(open(database, "rb"))
    for ctf in ctfs:
        if ctf.channel_id == ctf_channel_id:
            for challenge in ctf.challenges:
                if challenge.name == challenge_name:
                    return challenge

    return False


def get_challenge_by_channel_id(database, challenge_channel_id):
    """
    Fetch a Challenge object in the database with a given channel ID
    Return the matching Challenge object if found, or False otherwise.
    """
    ctfs = pickle.load(open(database, "rb"))
    for ctf in ctfs:
            for challenge in ctf.challenges:
                if challenge.channel_id == challenge_channel_id:
                    return challenge

    return False


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
