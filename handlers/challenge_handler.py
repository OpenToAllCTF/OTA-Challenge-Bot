import pickle
import re

from bottypes.ctf import *
from bottypes.challenge import *
from bottypes.player import *
from bottypes.command_descriptor import *
from handlers.handler_factory import *
from handlers.base_handler import *
from util.util import *
from util.slack_wrapper import *


class AddCTFCommand(Command):
    """Add and keep track of a new CTF."""

    def execute(self, slack_wrapper, args, channel_id, user_id):
        """Execute AddCTF command."""
        name = args[0]

        if len(name) > 10:
            raise InvalidCommand(
                "Command failed. CTF name must be <= 10 characters.")

        # Create the channel
        response = slack_wrapper.create_channel(name)

        # Validate that the channel was successfully created.
        if response['ok'] == False:
            raise InvalidCommand(
                "\"{}\" channel creation failed.\nError : {}".format(name, response['error']))

        # Add purpose tag for persistence
        purpose = dict(ChallengeHandler.CTF_PURPOSE)
        purpose['name'] = name
        purpose = json.dumps(purpose)
        channel = response['channel']['id']
        slack_wrapper.set_purpose(channel, purpose)

        # Invite user
        slack_wrapper.invite_user(user_id, channel)

        # New CTF object
        ctf = CTF(channel, name)

        # Update list of CTFs
        ctfs = pickle.load(open(ChallengeHandler.DB, "rb"))
        ctfs[ctf.channel_id] = ctf
        pickle.dump(ctfs, open(ChallengeHandler.DB, "wb"))

        # Notify people of new channel
        message = "Created channel #{}".format(
            response['channel']['name']).strip()
        slack_wrapper.post_message(channel_id, message)


class RenameChallengeCommand(Command):
    """Renames an existing challenge channel."""

    def execute(self, slack_wrapper, args, channel_id, user_id):
        old_name = args[0]
        new_name = args[1]

        # Validate that the user is in a CTF channel
        ctf = get_ctf_by_channel_id(ChallengeHandler.DB, channel_id)

        if not ctf:
            raise InvalidCommand(
                "Command failed. You are not in a CTF channel.")

        if len(new_name) > 10:
            raise InvalidCommand(
                "Command failed. Challenge name must be <= 10 characters.")

        old_channel_name = "{}-{}".format(ctf.name, old_name)
        new_channel_name = "{}-{}".format(ctf.name, new_name)

        # Get the channel id for the channel to rename
        challenge = get_challenge_by_name(
            ChallengeHandler.DB, old_name, ctf.channel_id)

        if not challenge:
            raise InvalidCommand(
                "Command failed. Challenge '{}' not found.".format(old_name))

        log.debug("Renaming channel {} to {}".format(channel_id, new_name))
        response = slack_wrapper.rename_channel(
            challenge.channel_id, new_channel_name, is_private=True)

        if not response['ok']:
            raise InvalidCommand("\"{}\" channel rename failed.\nError : {}".format(
                old_channel_name, response['error']))

        # Update channel purpose
        slack_wrapper.update_channel_purpose_name(
            challenge.channel_id, new_name, is_private=True)

        # Update database
        update_challenge_name(ChallengeHandler.DB,
                              challenge.channel_id, new_name)

        text = "Challenge `{}` renamed to `{}` (#{})".format(
            old_name, new_name, new_channel_name)
        slack_wrapper.post_message(channel_id, text)


class RenameCTFCommand(Command):
    """Renames an existing challenge channel."""

    def execute(self, slack_wrapper, args, channel_id, user_id):
        old_name = args[0]
        new_name = args[1]

        ctf = get_ctf_by_name(ChallengeHandler.DB, old_name)

        if not ctf:
            raise InvalidCommand(
                "Command failed. CTF '{}' not found.".format(old_name))

        if len(new_name) > 10:
            raise InvalidCommand(
                "Command failed. CTF name must be <= 10 characters.")

        text = "Renaming the CTF might take some time depending on active channels..."
        slack_wrapper.post_message(ctf.channel_id, text)

        # Rename the ctf channel
        response = slack_wrapper.rename_channel(ctf.channel_id, new_name)

        if not response['ok']:
            raise InvalidCommand("\"{}\" channel rename failed.\nError : {}".format(
                old_name, response['error']))

        # Update channel purpose
        slack_wrapper.update_channel_purpose_name(ctf.channel_id, new_name)

        # Update database
        update_ctf_name(ChallengeHandler.DB, ctf.channel_id, new_name)

        # Rename all challenge channels for this ctf
        for chall in ctf.challenges:
            RenameChallengeCommand().execute(
                slack_wrapper, [chall.name, chall.name], ctf.channel_id, user_id)

        text = "CTF `{}` renamed to `{}` (#{})".format(
            old_name, new_name, new_name)
        slack_wrapper.post_message(ctf.channel_id, text)


class AddChallengeCommand(Command):
    """
    Add and keep track of a new challenge for a given CTF.
    """

    def execute(self, slack_wrapper, args, channel_id, user_id):
        """Execute the AddChallenge command."""
        name = args[0]
        category = args[1] if len(args) > 1 else None

        # Validate that the user is in a CTF channel
        ctf = get_ctf_by_channel_id(ChallengeHandler.DB, channel_id)

        if not ctf:
            raise InvalidCommand(
                "Command failed. You are not in a CTF channel.")

        if len(name) > 10:
            raise InvalidCommand(
                "Command failed. Challenge name must be <= 10 characters.")

        # Create the challenge channel
        channel_name = "{}-{}".format(ctf.name, name)
        response = slack_wrapper.create_channel(channel_name, is_private=True)

        # Validate that the channel was created successfully
        if not response['ok']:
            raise InvalidCommand(
                "\"{}\" channel creation failed.\nError : {}".format(channel_name, response['error']))

        # Add purpose tag for persistence
        challenge_channel_id = response['group']['id']
        purpose = dict(ChallengeHandler.CHALL_PURPOSE)
        purpose['name'] = name
        purpose['ctf_id'] = ctf.channel_id
        purpose['category'] = category

        purpose = json.dumps(purpose)
        slack_wrapper.set_purpose(
            challenge_channel_id, purpose, is_private=True)

        # New Challenge
        challenge = Challenge(
            ctf.channel_id, challenge_channel_id, name, category)

        # Update database
        ctfs = pickle.load(open(ChallengeHandler.DB, "rb"))
        ctf = ctfs[ctf.channel_id]
        ctf.add_challenge(challenge)
        pickle.dump(ctfs, open(ChallengeHandler.DB, "wb"))

        # Notify the channel
        text = "New challenge *{0}* created in private channel (type `!working {0}` to join).".format(name)

        slack_wrapper.post_message(channel_id, text)


class StatusCommand(Command):
    """
    Get a status of the currently running CTFs.
    """

    def execute(self, slack_wrapper, args, channel_id, user_id):
        """Execute the Status command."""
        ctfs = pickle.load(open(ChallengeHandler.DB, "rb"))
        members = slack_wrapper.get_members()
        members = {m["id"]: m["name"]
                   for m in members['members'] if m.get("presence") == "active"}

        response = ""
        for ctf in ctfs.values():

            response += "*============= #{} =============*\n".format(ctf.name)
            solved = [c for c in ctf.challenges if c.is_solved]
            unsolved = [c for c in ctf.challenges if not c.is_solved]

            # Check if the CTF has any challenges
            if not solved and not unsolved:
                response += "*[ No challenges available yet ]*\n"
                continue

            # Solved challenges
            response += "* > Solved*\n" if solved else "\n"
            for challenge in solved:
                players = []
                response += ":tada: *{}* (Solved by : {})\n".format(
                    challenge.name, transliterate(", ".join(challenge.solver)))

            # Unsolved challenges
            response += "* > Unsolved*\n" if unsolved else "\n"
            for challenge in unsolved:

                # Get active players
                players = []
                for player_id in challenge.players:
                    if player_id in members:
                        players.append(members[player_id])

                response += "[{} active] *{}* {}: {}\n".format(len(players), challenge.name, "({})".format(challenge.category)
                                                               if challenge.category else "", transliterate(", ".join(players)))
            response += "\n"

        response = response.strip()

        if response == "":  # Response is empty
            response += "*There are currently no running CTFs*"

        slack_wrapper.post_message(channel_id, response)


class WorkingCommand(Command):
    """
    Mark a player as "working" on a challenge.
    """

    def execute(self, slack_wrapper, args, channel_id, user_id):
        """Execute the Working command."""
        challenge_name = args[0] if args else None

        # Validate that current channel is a CTF channel
        ctf = get_ctf_by_channel_id(ChallengeHandler.DB, channel_id)

        if not ctf:
            raise InvalidCommand(
                "Command failed. You are not in a CTF channel.")

        # Get challenge object for challenge name or channel id
        challenge = ""
        if challenge_name:
            challenge = get_challenge_by_name(ChallengeHandler.DB,
                                              challenge_name, channel_id)
        else:
            challenge = get_challenge_by_channel_id(ChallengeHandler.DB,
                                                    channel_id)

        if not challenge:
            raise InvalidCommand("This challenge does not exist.")

        # Invite user to challenge channel
        slack_wrapper.invite_user(
            user_id, challenge.channel_id, is_private=True)

        # Update database
        ctfs = pickle.load(open(ChallengeHandler.DB, "rb"))

        for ctf in ctfs.values():
            for chal in ctf.challenges:
                if chal.channel_id == challenge.channel_id:
                    chal.add_player(Player(user_id))

        pickle.dump(ctfs, open(ChallengeHandler.DB, "wb"))


class SolveCommand(Command):
    """
    Mark a challenge as solved.
    """

    def execute(self, slack_wrapper, args, channel_id, user_id):
        """Execute the Solve command."""
        challenge = ""

        if args:
            # Multiple arguments: Need to check if a challenge was specified or
            # not
            challenge_name = args[0]

            # Check if we're currently in a challenge channel
            curChallenge = get_challenge_by_channel_id(
                ChallengeHandler.DB, channel_id)

            if curChallenge:
                # User is in a challenge channel => Check for challenge by name
                # in parent ctf channel
                challenge = get_challenge_by_name(
                    ChallengeHandler.DB, challenge_name, curChallenge.ctf_channel_id)
            else:
                # User is in the ctf channel => Check for challenge by name in
                # current challenge
                challenge = get_challenge_by_name(
                    ChallengeHandler.DB, challenge_name, channel_id)

            if not challenge:
                challenge = get_challenge_by_channel_id(
                    ChallengeHandler.DB, channel_id)
                additional_args = args if args else []
            else:
                additional_args = args[1:] if len(args) > 1 else []
        else:
            # No arguments => direct way of resolving challenge
            challenge = get_challenge_by_channel_id(
                ChallengeHandler.DB, channel_id)

            additional_args = []

        if not challenge:
            raise InvalidCommand("This challenge does not exist.")

        additional_solver = []

        # Get solving member
        member = slack_wrapper.get_member(user_id)
        solver_list = [member['user']['name']]

        # Find additional members to add
        for add_solve in additional_args:
            user_obj = resolve_user_by_user_id(slack_wrapper, add_solve)

            if user_obj['ok']:
                add_solve = user_obj['user']['name']

            if add_solve not in solver_list:
                solver_list.append(add_solve)
                additional_solver.append(add_solve)

        # Update database
        ctfs = pickle.load(open(ChallengeHandler.DB, "rb"))

        for ctf in ctfs.values():
            for chal in ctf.challenges:
                if chal.channel_id == challenge.channel_id:
                    if not challenge.is_solved:
                        member = slack_wrapper.get_member(user_id)
                        solver_list = [member['user'][
                            'name']] + additional_solver

                        chal.mark_as_solved(solver_list)

                        pickle.dump(ctfs, open(ChallengeHandler.DB, "wb"))

                        # Update channel purpose
                        purpose = dict(ChallengeHandler.CHALL_PURPOSE)
                        purpose['name'] = challenge.name
                        purpose['ctf_id'] = ctf.channel_id
                        purpose['solved'] = solver_list
                        purpose = json.dumps(purpose)
                        slack_wrapper.set_purpose(
                            challenge.channel_id, purpose, is_private=True)

                        # Announce the CTF channel
                        help_members = ""

                        if additional_solver:
                            help_members = "(together with {})".format(", ".join(
                                additional_solver))

                        message = "@here *{}* : {} has solved the \"{}\" challenge {}".format(
                            challenge.name, member['user']['name'], challenge.name, help_members)
                        message += "."

                        slack_wrapper.post_message(ctf.channel_id, message)

                    break


class ArchiveCTFCommand(Command):
    """Archive the challenge channels for a given CTF."""

    def execute(self, slack_wrapper, args, channel_id, user_id):
        """Execute the ArchiveCTF command."""

        ctf = get_ctf_by_channel_id(ChallengeHandler.DB, channel_id)
        if not ctf:
            raise InvalidCommand(
                "Command failed. You are not in a CTF channel.")

        # Get list of challenges
        challenges = get_challenges_for_ctf_id(ChallengeHandler.DB, channel_id)

        message = "Archived the following channels :\n"
        for challenge in challenges:
            message += "- #{}-{}\n".format(ctf.name, challenge.name)
            slack_wrapper.archive_private_channel(challenge.channel_id)
            remove_challenge_by_channel_id(
                ChallengeHandler.DB, challenge.channel_id, ctf.channel_id)

        # Stop tracking the main CTF channel
        slack_wrapper.set_purpose(channel_id, "")
        remove_ctf_by_channel_id(ChallengeHandler.DB, ctf.channel_id)

        # Show confirmation message
        slack_wrapper.post_message(channel_id, message)

class ReloadCommand(Command):
    """Reload the ctf information from slack to reflect updates of channel purposes."""

    def execute(self, slack_wrapper, args, channel_id, user_id):
        """Execute the Reload command."""

        slack_wrapper.post_message(channel_id, "Updating CTFs and challenges...")
        ChallengeHandler.update_database_from_slack(slack_wrapper)
        slack_wrapper.post_message(channel_id, "Update finished...")


class ChallengeHandler(BaseHandler):
    """
    Manages everything related to challenge coordination.

    Commands :
    # Create a defcon-25-quals channel
    !ctf addctf "defcon 25 quals"

    # Create a web-100 channel
    !ctf addchallenge "web 100" "defcon 25 quals"

    # Kick member from other ctf challenge channels and invite the member to the web 100 channel
    !ctf working "web 100"

    # Get status of all CTFs
    !ctf status
    """

    DB = "databases/challenge_handler.bin"
    CTF_PURPOSE = {
        "ota_bot": "DO_NOT_DELETE_THIS",
        "name": "",
        "type": "CTF"
    }

    CHALL_PURPOSE = {
        "ota_bot": "DO_NOT_DELETE_THIS",
        "ctf_id": "",
        "name": "",
        "solved": "",
        "category": "",
        "type": "CHALLENGE",
    }

    def __init__(self):
        self.commands = {
            "addctf": CommandDesc(AddCTFCommand, "Adds a new ctf",    ["ctf_name"], None),
            "addchallenge": CommandDesc(AddChallengeCommand, "Adds a new challenge for current ctf", ["challenge_name"], ["challenge_category"]),
            "working": CommandDesc(WorkingCommand, "Show that you're working on a challenge", None, ["challenge_name"]),
            "status": CommandDesc(StatusCommand, "Show the status for all ongoing ctf's", None, None),
            "solve": CommandDesc(SolveCommand, "Mark a challenge as solved", None, ["challenge_name", "support_member"]),
            "renamechallenge": CommandDesc(RenameChallengeCommand, "Renames a challenge", ["old_challenge_name", "new_challenge_name"], None),
            "renamectf": CommandDesc(RenameCTFCommand, "Renames a ctf", ["old_ctf_name", "new_ctf_name"], None),
            "reload" : CommandDesc(ReloadCommand, "Reload ctf information from slack", None, None),
            "archivectf": CommandDesc(ArchiveCTFCommand, "Archive the challenges of a ctf", None, None, True)
        }

    @staticmethod
    def update_database_from_slack(slack_wrapper):
        """
        Reload the ctf and challenge information from slack.        
        """
        database = {}
        response = slack_wrapper.get_public_channels()

        # Find active CTF channels
        for channel in response['channels']:
            purpose = load_json(channel['purpose']['value'])

            if not channel['is_archived'] and purpose and "ota_bot" in purpose and purpose["type"] == "CTF":
                ctf = CTF(channel['id'], purpose['name'])
                database[ctf.channel_id] = ctf

        # Find active challenge channels
        response = slack_wrapper.get_private_channels()
        for channel in response['groups']:
            purpose = load_json(channel['purpose']['value'])

            if not channel['is_archived'] and \
               purpose and "ota_bot" in purpose and \
               purpose["type"] == "CHALLENGE":
                challenge = Challenge(
                    purpose["ctf_id"], channel['id'], purpose["name"], purpose.get("category"))
                ctf_channel_id = purpose["ctf_id"]
                solvers = purpose["solved"]
                ctf = database.get(ctf_channel_id)

                # Mark solved challenges
                if solvers:
                    challenge.mark_as_solved(solvers)

                if ctf:
                    for member_id in channel['members']:
                        if member_id != slack_wrapper.user_id:
                            challenge.add_player(Player(member_id))

                    ctf.add_challenge(challenge)

        # Create the database accordingly
        pickle.dump(database, open(ChallengeHandler.DB, "wb+"))

    def init(self, slack_wrapper):
        ChallengeHandler.update_database_from_slack(slack_wrapper)


# Register this handler
HandlerFactory.register("ctf", ChallengeHandler())
