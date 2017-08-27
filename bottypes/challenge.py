#!/usr/bin/env python3

class Challenge:
    def __init__(self, channel_id, name):
        """
            An object representation of an ongoing challenge.
            channel_id : The slack id for the associated channel
            name : The name of the challenge
        """

        self.channel_id = channel_id
        self.name = name
        self.players = []
        self.is_solved = False
        self.solver = None

    def mark_as_solved(self, solver_list):
        """
            Mark a challenge as solved.
            solver_list : List of usernames, that solved the challenge.
        """
        self.is_solved = True
        self.solver = solver_list

    def unmark_as_solved(self):
        """
            Unmark a challenge as solved.
        """
        self.is_solved = False
        self.solver = None

    def add_player(self, player):
        """
            Add a player to the list of working players
        """
        if not any(p.user_id == player.user_id for p in self.players):
            self.players.append(player)

    def remove_player(self, user_id):
        """
            Remove a player from the list of working players
            using a given slack user ID
        """
        self.players = [player for player in self.players if player.user_id != user_id]
