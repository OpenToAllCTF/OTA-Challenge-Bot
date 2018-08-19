class Tournament:

    def __init__(self, channel_id, name, category, organizer):
        """
        An object representation of an ongoing challenge.
        channel_id : The slack id for the associated channel
        name : The name of the challenge
        """

        self.channel_id = channel_id
        self.name = name
        self.category = category
        self.players = {}
        self.winners = {}
        self.accept_signups = True
        self.finished = False
        self.organizer = organizer
    
    def close_signups(self):
        """
        Stop accepting sign ups. Could be used if the organizer feels that there's
        too many people.
        """
        self.accept_signups = False

    def open_signups(self):
        """
        Accept signups. Negates stop_signups().
        """
        self.accept_signups = True

    def add_player(self, user_id):
        """
        Add a player to the list of participating players.
        """
        self.players[user_id] = user_id

    def remove_player(self, user_id):
        """
        Remove a player from the list of participating players using a given slack
        user ID.
        """
        try:
            del self.players[user_id]
        except KeyError:
            # TODO: Should we allow this to perculate up to the caller?
            pass
