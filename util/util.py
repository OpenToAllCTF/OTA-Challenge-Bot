import json
import pickle

from util.loghandler import *

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
    for c_id, ctf in ctfs.items():
        if c_id == channel_id:
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
    for _, ctf in ctfs.items():
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
    for challenge in ctfs[ctf_channel_id].challenges:
        if challenge.name == challenge_name:
            return challenge

    return None


def get_challenge_by_channel_id(database, challenge_channel_id):
    """
    Fetch a Challenge object in the database with a given channel ID
    Return the matching Challenge object if found, or None otherwise.
    """
    ctfs = pickle.load(open(database, "rb"))
    for _, ctf in ctfs.items():
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
    ctf = ctfs[ctf_channel_id]

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

    for _, ctf in ctfs.items():
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
    ctf = ctfs[ctf_channel_id]
    ctf.name = new_name
    pickle.dump(ctfs, open(database, "wb"))
