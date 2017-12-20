import time

class Challenge:

    def __init__(self, ctf_channel_id, channel_id, name, category):
        """
        An object representation of an ongoing challenge.
        channel_id : The slack id for the associated channel
        name : The name of the challenge
        """

        self.channel_id = channel_id
        self.ctf_channel_id = ctf_channel_id
        self.name = name
        self.category = category
        self.players = {}
        self.is_solved = False
        self.solver = None
        self.solve_date = 0

    def mark_as_solved(self, solver_list, solve_date=None):
        """
        Mark a challenge as solved.
        solver_list : List of usernames, that solved the challenge.
        solve_date : Time of solve (epoch) (None: current time / value: set to specified value).
        """
        self.is_solved = True
        self.solver = solver_list
        self.solve_date = solve_date or int(time.time())

    def unmark_as_solved(self):
        """
        Unmark a challenge as solved.
        """
        self.is_solved = False
        self.solver = None

    def add_player(self, player):
        """
        Add a player to the list of working players.
        """
        self.players[player.user_id] = player

    def remove_player(self, user_id):
        """
        Remove a player from the list of working players using a given slack
        user ID.
        """
        try:
            del self.players[player.user_id]
        except KeyError:
            # TODO: Should we allow this to perculate up to the caller?
            pass
