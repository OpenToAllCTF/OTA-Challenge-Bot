class CTF:

    def __init__(self, channel_id, name):
        """
        An object representation of an ongoing CTF.
        channel_id : The slack id for the associated channel
        name : The name of the CTF
        """

        self.channel_id = channel_id
        self.name = name
        self.challenges = []
        self.cred_user = ""
        self.cred_pw = ""
        self.cred_url = ""

    def add_challenge(self, challenge):
        """
        Add a challenge object to the list of challenges belonging
        to this CTF.
        challenge : A challenge object
        """
        self.challenges.append(challenge)
