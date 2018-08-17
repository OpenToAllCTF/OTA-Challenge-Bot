import json
import pickle

from util.loghandler import *
from bottypes.invalid_command import *

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
    except ValueError:
        return None
    return json_object


def transliterate(string):
    """
        Converts ascii characters to a unicode
        equivalent.
    """
    mapping = {
        "a": "ɑ",  # \xc9\x91
        "A": "А",  # \xd0\x90
        "e": "е",  # \xd0\xb5
        "E": "Е",  # \xd0\x95
        "i": "і",  # \xd1\x96
        "I": "І",  # \xd0\x86
        "o": "о",  # \xd0\xbe
        "O": "О",  # \xd0\x9e
        "u": "υ",  # \xcf\x85
        "U": "υ",  # \xcf\x85
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


def update_ctf(database, channel_id, update_func):
    """
    Fetch a CTF object in the database with a given channel ID,
    and apply update_func on it. Saves the ctf database afterwards.
    """
    with open(database, "rb") as f:
        ctfs = pickle.load(f)

    ctf = ctfs.get(channel_id)

    if ctf:
        update_func(ctf)

        with open(database, "wb") as f:
            pickle.dump(ctfs, f)

        return ctf

    return None


def get_ctf_by_name(database, name):
    """
    Fetch a CTF object in the database with a given name.
    Return the matching CTF object if found, or None otherwise.
    """
    ctfs = pickle.load(open(database, "rb"))
    for ctf in ctfs.values():
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

    if ctf_channel_id not in ctfs:
        raise InvalidCommand("Could not find corresponding ctf channel. Try reloading ctf data.")

    for challenge in ctfs[ctf_channel_id].challenges:
        if challenge.name == challenge_name:
            return challenge

    return None


def get_challenge_from_args(database, args, channel_id):
    """
    Helper method for getting the channel either from arguments or current channel.
    """
    # Multiple arguments: Need to check if a challenge was specified or not
    challenge_name = args[0].lower()

    # Check if we're currently in a challenge channel
    current_chal = get_challenge_by_channel_id(
        database, channel_id)

    if current_chal:
        # User is in a challenge channel => Check for challenge by name
        # in parent ctf channel
        challenge = get_challenge_by_name(
            database, challenge_name, current_chal.ctf_channel_id)
    else:
        # User is in the ctf channel => Check for challenge by name in
        # current challenge
        challenge = get_challenge_by_name(
            database, challenge_name, channel_id)

    return challenge


def get_challenge_by_channel_id(database, challenge_channel_id):
    """
    Fetch a Challenge object in the database with a given channel ID
    Return the matching Challenge object if found, or None otherwise.
    """
    ctfs = pickle.load(open(database, "rb"))
    for ctf in ctfs.values():
        for challenge in ctf.challenges:
            if challenge.channel_id == challenge_channel_id:
                return challenge

    return None


def get_challenges_for_user_id(database, user_id, ctf_channel_id):
    """
    Fetch a list of all challenges a user is working on for a given CTF.
    Return a list of matching Challenge objects.
    """

    ctfs = pickle.load(open(database, "rb"))
    ctf = ctfs[ctf_channel_id]

    challenges = []
    for challenge in ctf.challenges:
        if user_id in challenge.players:
            challenges.append(challenge)

    return challenges


def get_challenges_for_ctf_id(database, ctf_channel_id):
    """
    Fetch a list of all challenges of a given CTF.
    Return a list of matching Challenge objects.
    """

    ctfs = pickle.load(open(database, "rb"))
    ctf = ctfs[ctf_channel_id]

    challenges = []
    for challenge in ctf.challenges:
        challenges.append(challenge)

    return challenges


def update_challenge_name(database, challenge_channel_id, new_name):
    """
    Updates the name of the challenge with the specified challenge id
    """
    ctfs = pickle.load(open(database, "rb"))

    for ctf in ctfs.values():
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


def remove_challenge_by_channel_id(database, challenge_channel_id, ctf_channel_id):
    """
    Remove a challenge from the database using a given challenge and CTF id.
    """
    ctfs = pickle.load(open(database, "rb"))
    ctf = ctfs[ctf_channel_id]
    ctf.challenges = list(filter(lambda challenge: challenge.channel_id != challenge_channel_id, ctf.challenges))
    pickle.dump(ctfs, open(database, "wb"))


def remove_ctf_by_channel_id(database, ctf_channel_id):
    """
    Remove a CTF from the database using a given CTF id.
    """
    ctfs = pickle.load(open(database, "rb"))
    ctfs.pop(ctf_channel_id)
    pickle.dump(ctfs, open(database, "wb"))


def parse_user_id(user_id):
    """
    Parse a user_id, removing possible @-notation and make sure it's uppercase.
    """
    if user_id.startswith("<@") and user_id.endswith(">"):
        return user_id[2:-1].upper()

    return user_id.upper()


def resolve_user_by_user_id(slack_wrapper, user_id):
    """
    Resolve a user id to an user object.
    """
    return slack_wrapper.get_member(parse_user_id(user_id))


def get_display_name(member):
    return member['user']['profile']['display_name']
