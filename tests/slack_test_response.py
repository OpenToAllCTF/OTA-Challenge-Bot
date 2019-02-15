class SlackResponse:
    def __init__(self, message, channel):
        self.message = message
        self.channel = channel

    def __repr__(self):
        return "{} ({})".format(self.message, self.channel)

    def __str__(self):
        return "{} ({})".format(self.message, self.channel)
