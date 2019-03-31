from abc import ABC


class Command(ABC):
    """Defines the command interface."""

    def __init__(self):
        pass

    @classmethod
    def execute(cls, slack_wrapper, args, timestamp, channel_id, user_id, user_is_admin):
        pass
