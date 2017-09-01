class Player:
    """
    An object representation of a CTF player.
    """

    def __init__(self, user_id):
        """
        user_id : The slack ID of a user
        """
        self.user_id = user_id
