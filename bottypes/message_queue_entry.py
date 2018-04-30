class MessageQueueEntry:
    def __init__(self, channel_id, category, sender, message):
        self.channel_id = channel_id
        self.category = category
        self.sender = sender
        self.message = message

    def get_formatted_message(self):
        return "_{}_ *{}* : {}".format(self.category, self.sender, self.message)
