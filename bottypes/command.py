from abc import ABC, abstractmethod


class Command(ABC):
    """Defines the command interface."""

    def __init__(self): pass

    @classmethod
    def execute(cls, slack_client, args, user_id, channel_id): pass
