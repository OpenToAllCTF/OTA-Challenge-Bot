#!/usr/bin/env python3
from abc import ABC, abstractmethod

class Command(ABC):
    """
        The command interface to be used
    """
    def __init__(self): pass
    def execute(self, slack_client, args, user_id, channel_id): pass
