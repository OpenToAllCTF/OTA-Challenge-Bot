#!/usr/bin/env python3

class InvalidCommand(Exception):
    """
      Exception for invalid commands.
      The message should be the usage for that command.
    """
    def __init__(self, message):
        self.message = message
