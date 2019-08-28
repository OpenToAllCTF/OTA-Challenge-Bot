import pickle
import time
from random import randint
from dateutil.relativedelta import relativedelta

from bottypes.challenge import Challenge
from bottypes.command import Command
from bottypes.command_descriptor import CommandDesc
from bottypes.ctf import CTF
from bottypes.player import Player
from bottypes.reaction_descriptor import ReactionDesc
from handlers import handler_factory
from handlers.base_handler import BaseHandler
from util.loghandler import log
from util.solveposthelper import ST_GIT_SUPPORT, post_ctf_data
from util.util import *


class RollCommand(Command):
    """Roll the dice. ;)"""

    @classmethod
    def execute(cls, slack_wrapper, args, timestamp, channel_id, user_id, user_is_admin):
        """Execute Roll command."""
        val = randint(0, 100)

        member = slack_wrapper.get_member(user_id)
        display_name = get_display_name(member)

        message = "*{}* rolled the dice... *{}*".format(display_name, val)

        slack_wrapper.post_message(channel_id, message)

MAX_CHANNEL_NAME_LENGTH = 80
MAX_CTF_NAME_LENGTH = 40

class AddCTFCommand(Command):
    """Add and keep track of a new CTF."""

    @classmethod
    def execute(cls, slack_wrapper, args, timestamp, channel_id, user_id, user_is_admin):
        """Execute AddCTF command."""
        name = args[0].lower()
        long_name = " ".join(args[1:])

        # Don't allow incorrectly parsed long names
        if "<http" in long_name:
            raise InvalidCommand("Add CTF failed: Long name interpreted as link, try avoid using `.` in it.")

        if len(name) > MAX_CTF_NAME_LENGTH:
            raise InvalidCommand("Add CTF failed: CTF name must be <= {} characters.".format(MAX_CTF_NAME_LENGTH))

        # Check for invalid characters
        if not is_valid_name(name):
            raise InvalidCommand("Add CTF failed: Invalid characters for CTF name found.")

        # Create the channel
        response = slack_wrapper.create_channel(name)

        # Validate that the channel was successfully created.
        if not response['ok']:
            raise InvalidCommand("\"{}\" channel creation failed:\nError : {}".format(name, response['error']))

        ctf_channel_id = response['channel']['id']

        # New CTF object
        ctf = CTF(ctf_channel_id, name, long_name)

        # Update list of CTFs
        ctfs = pickle.load(open(ChallengeHandler.DB, "rb"))
        ctfs[ctf.channel_id] = ctf
        pickle.dump(ctfs, open(ChallengeHandler.DB, "wb"))

        # Add purpose tag for persistance
        ChallengeHandler.update_ctf_purpose(slack_wrapper, ctf)

        # Invite user
        slack_wrapper.invite_user(user_id, ctf_channel_id)

        # Invite everyone in the auto-invite list
        auto_invite_list = handler_factory.botserver.get_config_option("auto_invite")

        if type(auto_invite_list) == list:
            for invite_user_id in auto_invite_list:
                slack_wrapper.invite_user(invite_user_id, ctf_channel_id)

        # Notify people of new channel
        message = "Created channel #{}".format(response['channel']['name']).strip()
        slack_wrapper.post_message(channel_id, message)


class RenameChallengeCommand(Command):
    """Renames an existing challenge channel."""

    @classmethod
    def execute(cls, slack_wrapper, args, timestamp, channel_id, user_id, user_is_admin):
        old_name = args[0].lower()
        new_name = args[1].lower()

        # Validate that the user is in a CTF channel
        ctf = get_ctf_by_channel_id(ChallengeHandler.DB, channel_id)

        if not ctf:
            raise InvalidCommand("Rename challenge failed: You are not in a CTF channel.")

        if len(new_name) > (MAX_CHANNEL_NAME_LENGTH - len(ctf.name) - 1):
            raise InvalidCommand(
                "Rename challenge failed: Challenge name must be <= {} characters.".format(
                    MAX_CHANNEL_NAME_LENGTH - len(ctf.name) - 1))

        # Check for invalid characters
        if not is_valid_name(new_name):
            raise InvalidCommand("Command failed: Invalid characters for challenge name found.")

        old_channel_name = "{}-{}".format(ctf.name, old_name)
        new_channel_name = "{}-{}".format(ctf.name, new_name)

        # Get the channel id for the channel to rename
        challenge = get_challenge_by_name(ChallengeHandler.DB, old_name, ctf.channel_id)

        if not challenge:
            raise InvalidCommand("Rename challenge failed: Challenge '{}' not found.".format(old_name))

        log.debug("Renaming channel %s to %s", channel_id, new_name)
        response = slack_wrapper.rename_channel(challenge.channel_id, new_channel_name, is_private=True)

        if not response['ok']:
            raise InvalidCommand("\"{}\" channel rename failed:\nError: {}".format(old_channel_name, response['error']))

        # Update channel purpose
        slack_wrapper.update_channel_purpose_name(challenge.channel_id, new_name, is_private=True)

        # Update database
        update_challenge_name(ChallengeHandler.DB,
                              challenge.channel_id, new_name)

        text = "Challenge `{}` renamed to `{}` (#{})".format(old_name, new_name, new_channel_name)
        slack_wrapper.post_message(channel_id, text)


class RenameCTFCommand(Command):
    """Renames an existing challenge channel."""

    @classmethod
    def execute(cls, slack_wrapper, args, timestamp, channel_id, user_id, user_is_admin):
        old_name = args[0].lower()
        new_name = args[1].lower()

        ctf = get_ctf_by_name(ChallengeHandler.DB, old_name)

        if not ctf:
            raise InvalidCommand("Rename CTF failed: CTF '{}' not found.".format(old_name))

        ctflen = len(new_name)

        # pre-check challenges, if renaming would break channel name length
        for chall in ctf.challenges:
            if len(chall.name) + ctflen > MAX_CHANNEL_NAME_LENGTH - 1:
                raise InvalidCommand(
                    "Rename CTF failed: Challenge {} would break channel name length restriction.".format(chall.name))

        # still ctf name shouldn't be longer than 10 characters for allowing reasonable challenge names
        if len(new_name) > MAX_CTF_NAME_LENGTH:
            raise InvalidCommand("Rename CTF failed: CTF name must be <= {} characters.".format(MAX_CTF_NAME_LENGTH))

        # Check for invalid characters
        if not is_valid_name(new_name):
            raise InvalidCommand("Rename CTF failed: Invalid characters for CTF name found.")

        text = "Renaming the CTF might take some time depending on active channels..."
        slack_wrapper.post_message(ctf.channel_id, text)

        # Rename the ctf channel
        response = slack_wrapper.rename_channel(ctf.channel_id, new_name)

        if not response['ok']:
            raise InvalidCommand("\"{}\" channel rename failed:\nError : {}".format(old_name, response['error']))

        # Update channel purpose
        slack_wrapper.update_channel_purpose_name(ctf.channel_id, new_name)

        # Update database
        update_ctf_name(ChallengeHandler.DB, ctf.channel_id, new_name)

        # Rename all challenge channels for this ctf
        for chall in ctf.challenges:
            RenameChallengeCommand().execute(
                slack_wrapper, [chall.name, chall.name], timestamp, ctf.channel_id, user_id, user_is_admin)

        text = "CTF `{}` renamed to `{}` (#{})".format(old_name, new_name, new_name)
        slack_wrapper.post_message(ctf.channel_id, text)


class AddChallengeCommand(Command):
    """
    Add and keep track of a new challenge for a given CTF.
    """

    @classmethod
    def execute(cls, slack_wrapper, args, timestamp, channel_id, user_id, user_is_admin):
        """Execute the AddChallenge command."""
        name = args[0].lower()
        category = args[1] if len(args) > 1 else None

        # Validate that the user is in a CTF channel
        ctf = get_ctf_by_channel_id(ChallengeHandler.DB, channel_id)

        if not ctf:
            raise InvalidCommand("Add challenge failed: You are not in a CTF channel.")

        if len(name) > (MAX_CHANNEL_NAME_LENGTH - len(ctf.name) - 1):
            raise InvalidCommand(
                "Add challenge failed: Challenge name must be <= {} characters."
                .format(MAX_CHANNEL_NAME_LENGTH - len(ctf.name) - 1))

        # Check for invalid characters
        if not is_valid_name(name):
            raise InvalidCommand("Command failed: Invalid characters for challenge name found.")

        # Check for finished ctf
        if ctf.finished and not user_is_admin:
            raise InvalidCommand("Add challenge faild: CTF *{}* is over...".format(ctf.name))

        # Create the challenge channel
        channel_name = "{}-{}".format(ctf.name, name)
        response = slack_wrapper.create_channel(channel_name, is_private=True)

        # Validate that the channel was created successfully
        if not response['ok']:
            raise InvalidCommand("\"{}\" channel creation failed:\nError : {}".format(channel_name, response['error']))

        # Add purpose tag for persistence
        challenge_channel_id = response['group']['id']
        purpose = dict(ChallengeHandler.CHALL_PURPOSE)
        purpose['name'] = name
        purpose['ctf_id'] = ctf.channel_id
        purpose['category'] = category

        purpose = json.dumps(purpose)
        slack_wrapper.set_purpose(challenge_channel_id, purpose, is_private=True)

        # Invite everyone in the auto-invite list
        for invite_user_id in handler_factory.botserver.get_config_option("auto_invite"):
            slack_wrapper.invite_user(invite_user_id, challenge_channel_id, is_private=True)

        # New Challenge
        challenge = Challenge(ctf.channel_id, challenge_channel_id, name, category)

        # Update database
        ctfs = pickle.load(open(ChallengeHandler.DB, "rb"))
        ctf = ctfs[ctf.channel_id]
        ctf.add_challenge(challenge)
        pickle.dump(ctfs, open(ChallengeHandler.DB, "wb"))

        # Notify the channel
        text = "New challenge *{0}* created in private channel (type `!workon {0}` to join).".format(name)
        slack_wrapper.post_message(channel_id, text)


class RemoveChallengeCommand(Command):
    """
    Remove a challenge from the CTF.
    """

    @classmethod
    def execute(cls, slack_wrapper, args, timestamp, channel_id, user_id, user_is_admin):
        """Execute the RemoveChallenge command."""
        challenge_name = args[0].lower() if args else None

        # Validate that current channel is a CTF channel
        ctf = get_ctf_by_channel_id(ChallengeHandler.DB, channel_id)

        if not ctf:
            raise InvalidCommand("Remove challenge failed: You are not in a CTF channel.")

        # Get challenge object for challenge name or channel id
        challenge = ""
        if challenge_name:
            challenge = get_challenge_by_name(ChallengeHandler.DB, challenge_name, channel_id)
        else:
            challenge = get_challenge_by_channel_id(ChallengeHandler.DB, channel_id)

        if not challenge:
            raise InvalidCommand("This challenge does not exist.")

        # Remove the challenge channel and ctf challenge entry
        slack_wrapper.archive_private_channel(challenge.channel_id)
        remove_challenge_by_channel_id(ChallengeHandler.DB, challenge.channel_id, ctf.channel_id)

        # Show confirmation message
        member = slack_wrapper.get_member(user_id)
        display_name = get_display_name(member)

        slack_wrapper.post_message(
            ctf.channel_id, text="Challenge *{}* was removed by *{}*.".format(challenge.name, display_name))


class UpdateStatusCommand(Command):
    """
    Updates the status information, when the refresh reaction was clicked.
    """

    @classmethod
    def execute(cls, slack_wrapper, args, timestamp, channel_id, user_id, user_is_admin):
        """Execute the UpdateStatus command."""
        timestamp = args["timestamp"]

        # Check message content, if the emoji was placed on a status message
        # (no tagging atm, so just check it starts like a status message)
        result = slack_wrapper.get_message(channel_id, timestamp)

        if result["ok"] and result["messages"]:
            if "==========" in result["messages"][0]["text"]:
                # check if status contained a category and only update for category then
                category_match = re.search(r"=== .*? \[(.*?)\] ====", result["messages"][0]["text"], re.S)
                category = category_match.group(1) if category_match else ""

                status, _ = StatusCommand().build_status_message(slack_wrapper, None, channel_id, user_id, user_is_admin, True, category)

                slack_wrapper.update_message(channel_id, timestamp, status)


class UpdateShortStatusCommand(Command):
    """
    Updates short status information, when the refresh reaction was clicked.
    """

    @classmethod
    def execute(cls, slack_wrapper, args, timestamp, channel_id, user_id, user_is_admin):
        """Execute the UpdateStatus command."""
        timestamp = args["timestamp"]

        # Check message content, if the emoji was placed on a status message
        # (no tagging atm, so just check it starts like a status message)
        result = slack_wrapper.get_message(channel_id, timestamp)

        if result["ok"] and result["messages"]:
            if "solved /" in result["messages"][0]["text"]:
                status, _ = StatusCommand().build_status_message(slack_wrapper, None, channel_id, user_id, user_is_admin, False)

                slack_wrapper.update_message(channel_id, timestamp, status)


class StatusCommand(Command):
    """
    Get a status of the currently running CTFs.
    """

    @classmethod
    def build_short_status(cls, ctf_list):
        """Build short status list."""
        response = ""

        for ctf in ctf_list:
            # Build short status list
            solved = [c for c in ctf.challenges if c.is_solved]

            def get_finish_info(ctf):
                return "(finished {} ago)".format(cls.get_finished_string(ctf)) if ctf.finished_on else "(finished)"

            response += "*#{} : _{}_ [{} solved / {} total] {}*\n".format(
                ctf.name, ctf.long_name, len(solved), len(ctf.challenges), get_finish_info(ctf) if ctf.finished else "")

        response = response.strip()

        if response == "":  # Response is empty
            response += "*There are currently no running CTFs*"

        return response

    @classmethod
    def get_finished_string(cls, ctf):
        timespan = time.time()-ctf.finished_on

        if timespan < 3600:
            return "less than an hour"

        # https://stackoverflow.com/a/11157649
        attrs = ['years', 'months', 'days', 'hours']
        def human_readable(delta): return ['%d %s' % (getattr(delta, attr), getattr(delta, attr) > 1 and attr or attr[:-1])
                                           for attr in attrs if getattr(delta, attr)]

        return ', '.join(human_readable(relativedelta(seconds=timespan)))

    @classmethod
    def build_verbose_status(cls, slack_wrapper, ctf_list, check_for_finish, category):
        """Build verbose status list."""
        member_list = slack_wrapper.get_members()

        # Bail out, if we couldn't read member list
        if not "members" in member_list:
            raise InvalidCommand("Status failed. Could not refresh member list...")

        members = {m["id"]: get_display_name_from_user(m)
                   for m in member_list['members']}

        response = ""
        for ctf in ctf_list:
            # Build long status list
            solved = sorted([c for c in ctf.challenges if c.is_solved and (
                not category or c.category == category)], key=lambda x: x.solve_date)
            unsolved = [c for c in ctf.challenges if not c.is_solved and (not category or c.category == category)]

            # Don't show ctfs not having a category challenge if filter is active
            if category and not solved and not unsolved:
                continue

            response += "*============= #{} {} {}=============*\n".format(
                ctf.name, "(finished)" if ctf.finished else "", "[{}] ".format(category) if category else "")

            if ctf.finished and ctf.finished_on:
                response += "* > Finished {} ago*\n".format(cls.get_finished_string(ctf))

            # Check if the CTF has any challenges
            if check_for_finish and ctf.finished and not solved:
                response += "*[ No challenges solved ]*\n"
                continue
            elif not solved and not unsolved:
                response += "*[ No challenges available yet ]*\n"
                continue

            # Solved challenges
            response += "* > Solved*\n" if solved else ""
            for challenge in solved:
                players = []
                response += ":tada: *{}*{} (Solved by : {})\n".format(
                    challenge.name,
                    " ({})".format(challenge.category) if challenge.category else "",
                    transliterate(", ".join(challenge.solver)))

            # Unsolved challenges
            if not check_for_finish or not ctf.finished:
                response += "* > Unsolved*\n" if unsolved else "\n"
                for challenge in unsolved:

                    # Get active players
                    players = []
                    for player_id in challenge.players:
                        if player_id in members:
                            players.append(members[player_id])

                    response += "[{} active] *{}* {}: {}\n".format(len(players), challenge.name, "({})".format(challenge.category)
                                                                   if challenge.category else "", transliterate(", ".join(players)))

        response = response.strip()

        if response == "":  # Response is empty
            response += "*There are currently no running CTFs*"

        return response

    @classmethod
    def build_status_message(cls, slack_wrapper, args, channel_id, user_id, user_is_admin, verbose=True, category=""):
        """Gathers the ctf information and builds the status response."""
        ctfs = pickle.load(open(ChallengeHandler.DB, "rb"))

        # Check if the user is in a ctf channel
        current_ctf = get_ctf_by_channel_id(ChallengeHandler.DB, channel_id)

        if current_ctf:
            ctf_list = [current_ctf]
            check_for_finish = False
            verbose = True              # override verbose for ctf channels
        else:
            ctf_list = ctfs.values()
            check_for_finish = True

        if verbose:
            response = cls.build_verbose_status(slack_wrapper, ctf_list, check_for_finish, category)
        else:
            response = cls.build_short_status(ctf_list)

        return response, verbose

    @classmethod
    def execute(cls, slack_wrapper, args, timestamp, channel_id, user_id, user_is_admin):
        """Execute the Status command."""
        verbose = args[0] == "-v" if args else False

        if verbose:
            category = args[1] if len(args) > 1 else ""
        else:
            category = args[0] if args else ""

        response, verbose = cls.build_status_message(
            slack_wrapper, args, channel_id, user_id, user_is_admin, verbose, category)

        if verbose:
            slack_wrapper.post_message_with_react(channel_id, response, "arrows_clockwise")
        else:
            slack_wrapper.post_message_with_react(channel_id, response, "arrows_counterclockwise")


class WorkonCommand(Command):
    """
    Mark a player as "working" on a challenge.
    """

    @classmethod
    def execute(cls, slack_wrapper, args, timestamp, channel_id, user_id, user_is_admin):
        """Execute the Workon command."""
        challenge_name = args[0].lower() if args else None

        # Validate that current channel is a CTF channel
        ctf = get_ctf_by_channel_id(ChallengeHandler.DB, channel_id)

        if not ctf:
            raise InvalidCommand("Workon failed: You are not in a CTF channel.")

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

        # Don't allow joining already solved challenges (except after finish or for admins)
        if challenge.is_solved and not ctf.finished and not user_is_admin:
            raise InvalidCommand("This challenge is already solved.")

        # Invite user to challenge channel
        slack_wrapper.invite_user(user_id, challenge.channel_id, is_private=True)

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

    @classmethod
    def execute(cls, slack_wrapper, args, timestamp, channel_id, user_id, user_is_admin):
        """Execute the Solve command."""
        challenge = ""

        if args:
            challenge = get_challenge_from_args(ChallengeHandler.DB, args, channel_id)

            if not challenge:
                challenge = get_challenge_by_channel_id(ChallengeHandler.DB, channel_id)
                additional_args = args if args else []
            else:
                additional_args = args[1:] if len(args) > 1 else []
        else:
            # No arguments => direct way of resolving challenge
            challenge = get_challenge_by_channel_id(ChallengeHandler.DB, channel_id)

            additional_args = []

        if not challenge:
            raise InvalidCommand("This challenge does not exist.")

        additional_solver = []

        # Get solving member
        member = slack_wrapper.get_member(user_id)
        solver_list = [get_display_name(member)]

        # Find additional members to add
        for add_solve in additional_args:
            user_obj = resolve_user_by_user_id(slack_wrapper, add_solve)

            if user_obj['ok']:
                add_solve = get_display_name(user_obj)

            if add_solve not in solver_list:
                solver_list.append(add_solve)
                additional_solver.append(add_solve)

        # Update database
        ctfs = pickle.load(open(ChallengeHandler.DB, "rb"))

        for ctf in ctfs.values():
            for chal in ctf.challenges:
                if chal.channel_id == challenge.channel_id:
                    if not challenge.is_solved:
                        # Check for finished ctf
                        if ctf.finished and not user_is_admin:
                            raise InvalidCommand("Solve challenge faild: CTF *{}* is over...".format(ctf.name))

                        member = slack_wrapper.get_member(user_id)
                        solver_list = [get_display_name(member)] + additional_solver

                        chal.mark_as_solved(solver_list)

                        pickle.dump(ctfs, open(ChallengeHandler.DB, "wb"))

                        # Update channel purpose
                        purpose = dict(ChallengeHandler.CHALL_PURPOSE)
                        purpose['name'] = challenge.name
                        purpose['ctf_id'] = ctf.channel_id
                        purpose['solved'] = solver_list
                        purpose['solve_date'] = chal.solve_date
                        purpose['category'] = chal.category

                        purpose = json.dumps(purpose)
                        slack_wrapper.set_purpose(challenge.channel_id, purpose, is_private=True)

                        # Announce the CTF channel
                        help_members = ""

                        if additional_solver:
                            help_members = "(together with {})".format(", ".join(additional_solver))

                        message = "@here *{}* : {} has solved the \"{}\" challenge {}".format(
                            challenge.name, get_display_name(member), challenge.name, help_members)
                        message += "."

                        slack_wrapper.post_message(ctf.channel_id, message)

                    break


class UnsolveCommand(Command):
    """
    Mark a solved challenge as unsolved again.
    """

    @classmethod
    def execute(cls, slack_wrapper, args, timestamp, channel_id, user_id, user_is_admin):
        """Execute the Unsolve command."""
        challenge = ""

        if args:
            challenge = get_challenge_from_args(ChallengeHandler.DB, args, channel_id)

        if not challenge:
            challenge = get_challenge_by_channel_id(ChallengeHandler.DB, channel_id)

        if not challenge:
            raise InvalidCommand("This challenge does not exist.")

        # Update database
        ctfs = pickle.load(open(ChallengeHandler.DB, "rb"))

        for ctf in ctfs.values():
            for chal in ctf.challenges:
                if chal.channel_id == challenge.channel_id:
                    if challenge.is_solved:
                        member = slack_wrapper.get_member(user_id)

                        chal.unmark_as_solved()

                        pickle.dump(ctfs, open(ChallengeHandler.DB, "wb"))

                        # Update channel purpose
                        purpose = dict(ChallengeHandler.CHALL_PURPOSE)
                        purpose['name'] = challenge.name
                        purpose['ctf_id'] = ctf.channel_id
                        purpose['category'] = challenge.category

                        purpose = json.dumps(purpose)
                        slack_wrapper.set_purpose(challenge.channel_id, purpose, is_private=True)

                        # Announce the CTF channel
                        message = "@here *{}* : {} has reset the solve on the \"{}\" challenge.".format(
                            challenge.name, get_display_name(member), challenge.name)
                        slack_wrapper.post_message(ctf.channel_id, message)

                        return

                    raise InvalidCommand("This challenge isn't marked as solve.")


class ArchiveCTFCommand(Command):
    """Archive the challenge channels for a given CTF."""

    @classmethod
    def execute(cls, slack_wrapper, args, timestamp, channel_id, user_id, user_is_admin):
        """Execute the ArchiveCTF command."""
        no_post = args[0].lower() if args else None

        ctf = get_ctf_by_channel_id(ChallengeHandler.DB, channel_id)
        if not ctf or ctf.channel_id != channel_id:
            raise InvalidCommand("Archive CTF failed: You are not in a CTF channel.")

        # Post solves if git support is enabled
        if ST_GIT_SUPPORT:
            try:
                if not no_post:
                    if not ctf.long_name:
                        raise InvalidCommand(
                            "The CTF has no long name set. Please fix the ctf purpose and reload ctf data before archiving this ctf.")

                    solve_tracker_url = post_ctf_data(ctf, ctf.long_name)

                    message = "Post was successfully uploaded to: {}".format(solve_tracker_url)
                    slack_wrapper.post_message(channel_id, message)

            except Exception as ex:
                raise InvalidCommand(str(ex))

        # Get list of challenges
        challenges = get_challenges_for_ctf_id(ChallengeHandler.DB, channel_id)

        message = "Archived the following channels :\n"
        for challenge in challenges:
            message += "- #{}-{}\n".format(ctf.name, challenge.name)
            slack_wrapper.archive_private_channel(challenge.channel_id)
            remove_challenge_by_channel_id(ChallengeHandler.DB, challenge.channel_id, ctf.channel_id)

        # Remove possible configured reminders for this ctf
        cleanup_reminders(slack_wrapper, handler_factory, ctf)

        # Stop tracking the main CTF channel
        slack_wrapper.set_purpose(channel_id, "")
        remove_ctf_by_channel_id(ChallengeHandler.DB, ctf.channel_id)

        # Show confirmation message
        slack_wrapper.post_message(channel_id, message)

        # Archive the main CTF channel also to cleanup
        slack_wrapper.archive_public_channel(channel_id)


class EndCTFCommand(Command):
    """
    Mark the ctf as finished, not allowing new challenges to be added, and don't show the ctf anymore
    in the status list.
    """

    @classmethod
    def handle_archive_reminder(cls, slack_wrapper, ctf):
        """Sets a reminder for admins to archive this ctf in a set time."""
        reminder_offset = handler_factory.botserver.get_config_option("archive_ctf_reminder_offset")

        if not reminder_offset:
            return

        admin_users = handler_factory.botserver.get_config_option("admin_users")

        if not admin_users:
            return

        msg = "CTF {} - {} (#{}) should be archived.".format(ctf.name, ctf.long_name, ctf.name)

        for admin in admin_users:
            slack_wrapper.add_reminder_hours(admin, msg, reminder_offset)

    @classmethod
    def execute(cls, slack_wrapper, args, timestamp, channel_id, user_id, user_is_admin):
        """Execute the EndCTF command."""

        ctf = get_ctf_by_channel_id(ChallengeHandler.DB, channel_id)
        if not ctf:
            raise InvalidCommand("End CTF failed: You are not in a CTF channel.")

        if ctf.finished:
            raise InvalidCommand("CTF is already marked as finished...")

        def update_func(ctf):
            ctf.finished = True
            ctf.finished_on = time.time()

        # Update database
        ctf = update_ctf(ChallengeHandler.DB, ctf.channel_id, update_func)

        if ctf:
            ChallengeHandler.update_ctf_purpose(slack_wrapper, ctf)
            cls.handle_archive_reminder(slack_wrapper, ctf)
            slack_wrapper.post_message(channel_id, "CTF *{}* finished...".format(ctf.name))


class ReloadCommand(Command):
    """Reload the ctf information from slack to reflect updates of channel purposes."""

    @classmethod
    def execute(cls, slack_wrapper, args, timestamp, channel_id, user_id, user_is_admin):
        """Execute the Reload command."""

        slack_wrapper.post_message(channel_id, "Updating CTFs and challenges...")
        ChallengeHandler.update_database_from_slack(slack_wrapper)
        slack_wrapper.post_message(channel_id, "Update finished...")


class AddCredsCommand(Command):
    """Add credential informations for current ctf."""

    @classmethod
    def execute(cls, slack_wrapper, args, timestamp, channel_id, user_id, user_is_admin):
        """Execute the AddCreds command."""

        cur_ctf = get_ctf_by_channel_id(ChallengeHandler.DB, channel_id)
        if not cur_ctf:
            raise InvalidCommand("Add Creds failed:. You are not in a CTF channel.")

        def update_func(ctf):
            ctf.cred_user = args[0]
            ctf.cred_pw = args[1]

        # Update database
        ctf = update_ctf(ChallengeHandler.DB, cur_ctf.channel_id, update_func)

        if ctf:
            ChallengeHandler.update_ctf_purpose(slack_wrapper, ctf)

            ctf_cred_url = args[2] if len(args) > 2 else ""

            if ctf_cred_url:
                slack_wrapper.set_topic(channel_id, ctf_cred_url)

            message = "Credentials for CTF *{}* updated...".format(ctf.name)
            slack_wrapper.post_message(channel_id, message)


class ShowCredsCommand(Command):
    """Shows credential informations for current ctf."""

    @classmethod
    def execute(cls, slack_wrapper, args, timestamp, channel_id, user_id, user_is_admin):
        """Execute the ShowCreds command."""

        cur_ctf = get_ctf_by_channel_id(ChallengeHandler.DB, channel_id)
        if not cur_ctf:
            raise InvalidCommand("Show creds failed: You are not in a CTF channel.")

        if cur_ctf.cred_user and cur_ctf.cred_pw:
            message = "Credentials for CTF *{}*\n".format(cur_ctf.name)
            message += "```"
            message += "Username : {}\n".format(cur_ctf.cred_user)
            message += "Password : {}\n".format(cur_ctf.cred_pw)
            message += "```"
        else:
            message = "No credentials provided for CTF *{}*.".format(cur_ctf.name)

        slack_wrapper.post_message(channel_id, message, "", parse=None)


class ChallengeHandler(BaseHandler):
    """
    Manages everything related to challenge coordination.

    Commands :
    # Create a defcon-25-quals channel
    !ctf addctf "defcon 25 quals"

    # Create a web-100 channel
    !ctf addchallenge "web 100" "defcon 25 quals"

    # Kick member from other ctf challenge channels and invite the member to the web 100 channel
    !ctf workon "web100"

    # Get status of all CTFs
    !ctf status
    """

    DB = "databases/challenge_handler.bin"
    CTF_PURPOSE = {
        "ota_bot": "OTABOT",
        "name": "",
        "type": "CTF",
        "cred_user": "",
        "cred_pw": "",
        "long_name": "",
        "finished": False
    }

    CHALL_PURPOSE = {
        "ota_bot": "OTABOT",
        "ctf_id": "",
        "name": "",
        "solved": "",
        "category": "",
        "type": "CHALLENGE",
    }

    def __init__(self):
        self.commands = {
            "addctf": CommandDesc(AddCTFCommand, "Adds a new ctf", ["ctf_name", "long_name"], None),
            "addchallenge": CommandDesc(AddChallengeCommand, "Adds a new challenge for current ctf", ["challenge_name", "challenge_category"], None),
            "workon": CommandDesc(WorkonCommand, "Show that you're working on a challenge", None, ["challenge_name"]),
            "status": CommandDesc(StatusCommand, "Show the status for all ongoing ctf's", None, ["category"]),
            "solve": CommandDesc(SolveCommand, "Mark a challenge as solved", None, ["challenge_name", "support_member"]),
            "renamechallenge": CommandDesc(RenameChallengeCommand, "Renames a challenge", ["old_challenge_name", "new_challenge_name"], None),
            "renamectf": CommandDesc(RenameCTFCommand, "Renames a ctf", ["old_ctf_name", "new_ctf_name"], None),
            "reload": CommandDesc(ReloadCommand, "Reload ctf information from slack", None, None, True),
            "archivectf": CommandDesc(ArchiveCTFCommand, "Archive the challenges of a ctf", None, ["nopost"], True),
            "endctf": CommandDesc(EndCTFCommand, "Mark a ctf as ended, but not archive it directly", None, None, True),
            "addcreds": CommandDesc(AddCredsCommand, "Add credentials for current ctf", ["ctf_user", "ctf_pw"], ["ctf_url"]),
            "showcreds": CommandDesc(ShowCredsCommand, "Show credentials for current ctf", None, None),
            "unsolve": CommandDesc(UnsolveCommand, "Remove solve of a challenge", None, ["challenge_name"]),
            "removechallenge": CommandDesc(RemoveChallengeCommand, "Remove challenge", None, ["challenge_name"], True),
            "roll": CommandDesc(RollCommand, "Roll the dice", None, None)
        }
        self.reactions = {
            "arrows_clockwise": ReactionDesc(UpdateStatusCommand),
            "arrows_counterclockwise": ReactionDesc(UpdateShortStatusCommand)
        }
        self.aliases = {
            "finishctf": "endctf",
            "addchall": "addchallenge",
        }

    @staticmethod
    def update_ctf_purpose(slack_wrapper, ctf):
        """
        Update the purpose for the ctf channel.
        """
        purpose = dict(ChallengeHandler.CTF_PURPOSE)
        purpose["ota_bot"] = "OTABOT"
        purpose["name"] = ctf.name
        purpose["type"] = "CTF"
        purpose["cred_user"] = ctf.cred_user
        purpose["cred_pw"] = ctf.cred_pw
        purpose["long_name"] = ctf.long_name
        purpose["finished"] = ctf.finished
        purpose["finished_on"] = ctf.finished_on

        slack_wrapper.set_purpose(ctf.channel_id, purpose)

    @staticmethod
    def update_database_from_slack(slack_wrapper):
        """
        Reload the ctf and challenge information from slack.
        """
        database = {}
        privchans = slack_wrapper.get_private_channels()["groups"]
        pubchans = slack_wrapper.get_public_channels()["channels"]

        # Find active CTF channels
        for channel in [*privchans, *pubchans]:
            try:
                purpose = load_json(channel['purpose']['value'])

                if not channel['is_archived'] and purpose and "ota_bot" in purpose and purpose["type"] == "CTF":
                    ctf = CTF(channel['id'], purpose['name'], purpose['long_name'])

                    ctf.cred_user = purpose.get("cred_user", "")
                    ctf.cred_pw = purpose.get("cred_pw", "")
                    ctf.finished = purpose.get("finished", False)
                    ctf.finished_on = purpose.get("finished_on", 0)

                    database[ctf.channel_id] = ctf
            except:
                pass

        # Find active challenge channels
        response = slack_wrapper.get_private_channels()
        for channel in response['groups']:
            try:
                purpose = load_json(channel['purpose']['value'])

                if not channel['is_archived'] and purpose and "ota_bot" in purpose and purpose["type"] == "CHALLENGE":
                    challenge = Challenge(purpose["ctf_id"], channel['id'], purpose["name"], purpose.get("category"))
                    ctf_channel_id = purpose["ctf_id"]
                    solvers = purpose["solved"]
                    ctf = database.get(ctf_channel_id)

                    # Mark solved challenges
                    if solvers:
                        challenge.mark_as_solved(solvers, purpose.get("solve_date"))

                    if ctf:
                        for member_id in channel['members']:
                            if member_id != slack_wrapper.user_id:
                                challenge.add_player(Player(member_id))

                        ctf.add_challenge(challenge)
            except:
                pass

        # Create the database accordingly
        pickle.dump(database, open(ChallengeHandler.DB, "wb+"))

    def init(self, slack_wrapper):
        ChallengeHandler.update_database_from_slack(slack_wrapper)


# Register this handler
handler_factory.register("ctf", ChallengeHandler())
