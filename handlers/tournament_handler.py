import pickle

from bottypes.tournament import *
from bottypes.player import *
from bottypes.command_descriptor import *
from bottypes.reaction_descriptor import *
import handlers.handler_factory as handler_factory
from handlers.base_handler import *
from util.util import *
from util.slack_wrapper import *
from util.solveposthelper import *
from util.githandler import *
from util.ctf_template_resolver import *


class AddTournamentCommand(Command):
    """Add and keep track of a new tournament."""

    @classmethod
    def categories_count(self, tournaments):
        """Get the number of tournaments for each category"""
        categories = {}
        for tournament in tournaments.values():
            categories[tournament.category] = categories.get(tournament.category, 0) + 1
        return categories

    @classmethod
    def execute(self, slack_wrapper, args, channel_id, user_id, user_is_admin):
        """Execute AddTournament command."""
        category = args[0]

        # get lists of tournaments to give this one a number
        tournaments = pickle.load(open(TournamentHandler.DB, "rb"))
        counts = self.categories_count(tournaments)
        name = "{}-off{}".format(category, counts.get(category, 0) + 1)

        # Create the channel
        response = slack_wrapper.create_channel(name)

        # Validate that the channel was successfully created.
        if response['ok'] == False:
            raise InvalidCommand(
                "\"{}\" channel creation failed.\nError : {}".format(name, response['error']))

        tournament_channel_id = response['channel']['id']

        # Invite user
        slack_wrapper.invite_user(user_id, tournament_channel_id)

        # New Tournament object
        tournament = Tournament(tournament_channel_id, name, category, user_id)

        # Update list of Tournaments
        tournaments[tournament.channel_id] = tournament
        pickle.dump(tournaments, open(TournamentHandler.DB, "wb"))

        # Add purpose tag for persistence
        TournamentHandler.update_tournament_purpose(slack_wrapper, tournament)

        # Notify people of new channel
        message = "Created tournament #{}".format(
            response['channel']['name']).strip()
        slack_wrapper.post_message_with_react(channel_id, message, "crossed_swords")


class StatusCommand(Command):
    """
    Get a status of the currently running Tournaments.
    """

    @classmethod
    def build_tournament_title(self, tournament):
        response = "#{} [{} players]".format(tournament.name, len(tournament.players))
        
        if tournament.finished:
            response += " (tournament has ended)"
        elif not tournament.accept_signups:
            response += " (signups have closed)"

        return response

    @classmethod
    def build_short_status(self, tournaments):
        """Build short status list."""
        if len(tournaments) == 0:
            return "*There are currently no running tournaments*"
            
        message = ""

        for tournament in tournaments:
            message += "*{}*\n".format(self.build_tournament_title(tournament))

        return message

    @classmethod
    def build_verbose_status(self, slack_wrapper, tournaments):
        """Build verbose status list."""
        members = slack_wrapper.get_members()

        # Bail out, if we couldn't read member list
        if not "members" in members:
            raise InvalidCommand("Status failed. Could not refresh member list...")

        members = {m["id"]: m["profile"]["display_name"] for m in members['members']}

        message = ""
        for tournament in tournaments:
            message += "*------------- {} -------------*\n".format(
                self.build_tournament_title(tournament))

            if len(tournament.players) == 0:
                message += "*There are currently no participants in this tournament.*\n"
                continue

            message += "*Players for this tournament are*\n```\n"

            # Get players
            for player_id in tournament.players:
                if player_id in members:
                    message += "{}\n".format(members[player_id])

            message += "```\n"
            
        return message

    @classmethod
    def build_status_message(self, slack_wrapper, args, channel_id, user_id, user_is_admin, verbose=True):
        """Gathers the ctf information and builds the status response."""
        tournaments = pickle.load(open(TournamentHandler.DB, "rb"))

        # Check if the user is in a ctf channel
        current_tournament = get_tournament_by_channel_id(TournamentHandler.DB, channel_id)

        if current_tournament:
            tournaments = [current_tournament]
            verbose = True              # override verbose for ctf channels
        else:
            tournaments = list(tournaments.values())

        if verbose:
            response = self.build_verbose_status(slack_wrapper, tournaments)
        else:
            response = self.build_short_status(tournaments)

        return response, verbose

    @classmethod
    def execute(self, slack_wrapper, args, channel_id, user_id, user_is_admin):
        """Execute the Status command."""
        verbose = args[0] == "-v" if len(args) > 0 else False

        response, verbose = self.build_status_message(slack_wrapper, args, channel_id, user_id, user_is_admin, verbose)

        if verbose:
            slack_wrapper.post_message_with_react(channel_id, response, "arrows_clockwise")
        else:
            slack_wrapper.post_message_with_react(channel_id, response, "arrows_counterclockwise")


class UpdateStatusCommand(Command):
    """
    Updates the status information, when the refresh reaction was clicked.
    """

    @classmethod
    def execute(cls, slack_wrapper, args, channel_id, user_id, user_is_admin):
        """Execute the UpdateStatus command."""
        timestamp = args["timestamp"]

        # Check message content, if the emoji was placed on a status message
        # (no tagging atm, so just check it starts like a status message)
        result = slack_wrapper.get_message(channel_id, timestamp)

        if result["ok"] and result["messages"]:
            if "-------" in result["messages"][0]["text"]:
                status, _ = StatusCommand().build_status_message(slack_wrapper, None, channel_id, user_id, user_is_admin, True)

                slack_wrapper.update_message(channel_id, timestamp, status)


class UpdateShortStatusCommand(Command):
    """
    Updates short status information, when the refresh reaction was clicked.
    """

    @classmethod
    def execute(cls, slack_wrapper, args, channel_id, user_id, user_is_admin):
        """Execute the UpdateStatus command."""
        timestamp = args["timestamp"]

        # Check message content, if the emoji was placed on a status message
        # (no tagging atm, so just check it starts like a status message)
        result = slack_wrapper.get_message(channel_id, timestamp)

        if result["ok"] and result["messages"]:
            if "players" in result["messages"][0]["text"]:
                status, _ = StatusCommand().build_status_message(slack_wrapper, None, channel_id, user_id, user_is_admin, False)

                slack_wrapper.update_message(channel_id, timestamp, status)


class JoinCommand(Command):
    """
    Mark a player as participating a tournament.
    """

    @classmethod
    def execute(self, slack_wrapper, args, channel_id, user_id, user_is_admin):
        """Execute the Play command."""

        # Validate that current channel is a tournament channel
        tournament = get_tournament_by_channel_id(TournamentHandler.DB, channel_id)

        if not tournament:
            raise InvalidCommand(
                "Command failed. You are not in a tournament channel.")

        if tournament.finished:
            raise InvalidCommand(
                "Command failed. Tournament has ended.")

        if user_id in tournament.players:
            raise InvalidCommand(
                "Command failed. You have already signed up for this tournament.")

        if not tournament.accept_signups:
            raise InvalidCommand(
                "Command failed. Signups have closed for this tournament.")
    
        # Update database
        def update_func(tournament):
            tournament.add_player(user_id)

        tournament = update_tournament(TournamentHandler.DB, channel_id, update_func)
        TournamentHandler.update_tournament_purpose(slack_wrapper, tournament)

        slack_wrapper.post_message(user_id, "You have signed up for #{}.".format(tournament.name))


class UnjoinCommand(Command):
    """
    Mark a player as no longer participating a tournament.
    """

    @classmethod
    def execute(self, slack_wrapper, args, channel_id, user_id, user_is_admin):
        """Execute the Play command."""

        # Validate that current channel is a tournament channel
        tournament = get_tournament_by_channel_id(TournamentHandler.DB, channel_id)

        if not tournament:
            raise InvalidCommand(
                "Command failed. You are not in a tournament channel.")

        if tournament.finished:
            raise InvalidCommand(
                "Command failed. Tournament has ended.")

        if not user_id in tournament.players:
            raise InvalidCommand(
                "Command failed. You have not signed up for this tournament.")

        if not tournament.accept_signups:
            raise InvalidCommand(
                "Command failed. Signups have closed for this tournament.")

        # Update database
        def update_func(tournament):
            tournament.remove_player(user_id)

        tournament = update_tournament(TournamentHandler.DB, channel_id, update_func)
        TournamentHandler.update_tournament_purpose(slack_wrapper, tournament)

        slack_wrapper.post_message(user_id, "You have pulled out from #{}.".format(tournament.name))


class JoinButtonCommand(Command):
    """
    Adds user as a player of a tournament through clicking the emoji.
    """

    @classmethod
    def execute(cls, slack_wrapper, args, channel_id, user_id, user_is_admin):
        """Execute the PlayTournament command."""
        timestamp = args["timestamp"]

        # Check message content, if the emoji was placed on a status message
        # (no tagging atm, so just check it starts like a status message)
        result = slack_wrapper.get_message(channel_id, timestamp)
        text = result["messages"][0]["text"]
        # Example: "Created tournament <#CCB9GMTD3|pwn-off1>"
        channel_name = text[text.index("|") + 1:-1]

        tournament = get_tournament_by_name(TournamentHandler.DB, channel_name)
        slack_wrapper.invite_user(user_id, tournament.channel_id)

        if not tournament.accept_signups:
            slack_wrapper.post_message(user_id, "Signups have closed for #{}.".format(
                tournament.name))
        elif tournament.finished:
            slack_wrapper.post_message(user_id, "{} has ended.".format(tournament.name))
        else:
            # Update database
            def update_func(tournament):
                tournament.add_player(user_id)

            tournament = update_tournament(TournamentHandler.DB, tournament.channel_id, update_func)
            TournamentHandler.update_tournament_purpose(slack_wrapper, tournament)

            slack_wrapper.post_message(user_id, "You have signed up for #{}.".format(tournament.name))


class CloseSignupsCommand(Command):
    """
    Close signups for this tournament.
    """

    @classmethod
    def execute(cls, slack_wrapper, args, channel_id, user_id, user_is_admin):
        """Execute the CloseSignups command"""
        tournament = get_tournament_by_channel_id(TournamentHandler.DB, channel_id)

        if not tournament:
            raise InvalidCommand(
                "Close signups failed. You are not in a tournament channel.")

        if user_id != tournament.organizer:
            raise InvalidCommand(
                "Command failed. You are not the organizer of this tournament.")

        if tournament.finished:
            raise InvalidCommand(
                "Command failed. Tournament has ended.")

        if not tournament.accept_signups:
            raise InvalidCommand(
                "Command failed. Signups are already closed.")

        def update_func(tournament):
            tournament.close_signups()

        tournament = update_tournament(TournamentHandler.DB, channel_id, update_func)
        TournamentHandler.update_tournament_purpose(slack_wrapper, tournament)

        slack_wrapper.post_message(channel_id, "Signups are closed for this tournament")


class OpenSignupsCommand(Command):
    """
    Open signups for this tournament.
    """

    @classmethod
    def execute(cls, slack_wrapper, args, channel_id, user_id, user_is_admin):
        """Execute the OpenSignups command"""
        tournament = get_tournament_by_channel_id(TournamentHandler.DB, channel_id)

        if not tournament:
            raise InvalidCommand(
                "Open signups failed. You are not in a tournament channel.")

        if user_id != tournament.organizer:
            raise InvalidCommand(
                "Command failed. You are not the organizer of this tournament.")

        if tournament.finished:
            raise InvalidCommand(
                "Command failed. Tournament has ended.")

        if tournament.accept_signups:
            raise InvalidCommand(
                "Command failed. Signups are already opened.")

        def update_func(tournament):
            tournament.open_signups()

        tournament = update_tournament(TournamentHandler.DB, channel_id, update_func)
        TournamentHandler.update_tournament_purpose(slack_wrapper, tournament)

        slack_wrapper.post_message(channel_id, "Signups are opened for this tournament")


class EndTournamentCommand(Command):
    """
    Mark the tournament as finished, and don't show the tournament anymore
    in the status list.
    """

    @classmethod
    def execute(cls, slack_wrapper, args, channel_id, user_id, user_is_admin):
        """Execute the EndTournament command."""

        tournament = get_tournament_by_channel_id(TournamentHandler.DB, channel_id)

        if not tournament:
            raise InvalidCommand("End tournament failed: You are not in a tournament channel.")

        if user_id != tournament.organizer:
            raise InvalidCommand(
                "Command failed. You are not the organizer of this tournament.")

        def update_func(tournament):
            tournament.finished = True

        # Update database
        tournament = update_tournament(TournamentHandler.DB, tournament.channel_id, update_func)

        if tournament:
            TournamentHandler.update_tournament_purpose(slack_wrapper, tournament)
            slack_wrapper.post_message(channel_id, "Tournament *{}* has ended...".format(tournament.name))


class ReloadCommand(Command):
    """Reload the tournament information from slack to reflect updates of channel purposes."""

    @classmethod
    def execute(cls, slack_wrapper, args, channel_id, user_id, user_is_admin):
        """Execute the Reload command."""

        slack_wrapper.post_message(channel_id, "Updating tournaments...")
        TournamentHandler.update_database_from_slack(slack_wrapper)
        slack_wrapper.post_message(channel_id, "Update finished...")


class TournamentHandler(BaseHandler):
    """
    Manages everything related to tournament coordination.

    Commands :
    # Create a pwn-off channel
    !tournament add "pwn"

    # Get status of tournaments
    !tournament status

    # Participate in the tournament
    !tournament join

    # Pull out from the tournament
    !tournament unjoin

    # Close signups for the tournament
    !tournament close-signups

    # Open signups for the tournament
    !tournament open-signups

    # End tournament
    !tournament end
    """

    DB = "databases/tournament_handler.bin"
    TOURNAMENT_PURPOSE = {
        "ota_bot": "DO_NOT_DELETE_THIS",
        "name": "",
        "type": "TOURNAMENT",
        "category": ""
    }

    def __init__(self):
        self.commands = {
            "add": CommandDesc(AddTournamentCommand, "Adds a new tournament", ["category"], None),
            "status": CommandDesc(StatusCommand, "Show the status for all ongoing tournaments", None, None),
            "join": CommandDesc(JoinCommand, "Participate in a tournament", None, None),
            "unjoin": CommandDesc(UnjoinCommand, "Participate in a tournament", None, None),
            "close-signups": CommandDesc(CloseSignupsCommand, "Close signups for this tournament", None, None),
            "open-signups": CommandDesc(OpenSignupsCommand, "Open signups for this tournament", None, None),
            "reload": CommandDesc(ReloadCommand, "Reload tournament information from slack", None, None),
            "end": CommandDesc(EndTournamentCommand, "Mark a tournament as ended, but not archive it directly", None, None, None),
        }
        self.reactions = {
            "arrows_clockwise": ReactionDesc(UpdateStatusCommand),
            "arrows_counterclockwise": ReactionDesc(UpdateShortStatusCommand),
            "crossed_swords": ReactionDesc(JoinButtonCommand)
        }

    @staticmethod
    def update_tournament_purpose(slack_wrapper, tournament):
        """
        Update the purpose for the tournament channel.
        """
        purpose = dict(TournamentHandler.TOURNAMENT_PURPOSE)
        purpose["ota_bot"] = "DO_NOT_DELETE_THIS"
        purpose["name"] = tournament.name
        purpose["category"] = tournament.category
        purpose["type"] = "TOURNAMENT"
        purpose["organizer"] = tournament.organizer
        purpose["accept_signups"] = tournament.accept_signups
        purpose["finished"] = tournament.finished
        purpose["players"] = tournament.players

        slack_wrapper.set_purpose(tournament.channel_id, purpose)

    @staticmethod
    def update_database_from_slack(slack_wrapper):
        """
        Reload the tournament and challenge information from slack.
        """
        database = {}
        privchans = slack_wrapper.get_private_channels()["groups"]
        pubchans = slack_wrapper.get_public_channels()["channels"]

        # Find active tournament channels
        for channel in [*privchans, *pubchans]:
            purpose = load_json(channel['purpose']['value'])

            if not channel['is_archived'] and purpose and "ota_bot" in purpose and purpose["type"] == "TOURNAMENT":
                tournament = Tournament(channel['id'], purpose['name'], purpose['category'], purpose['organizer'])

                tournament.finished = purpose.get("finished", False)
                tournament.accept_signups = purpose.get("accept_signups", True)
                tournament.players = purpose.get("players", {})

                database[tournament.channel_id] = tournament

        # Create the database accordingly
        pickle.dump(database, open(TournamentHandler.DB, "wb+"))

    def init(self, slack_wrapper):
        TournamentHandler.update_database_from_slack(slack_wrapper)


# Register this handler
handler_factory.register("tournament", TournamentHandler())
