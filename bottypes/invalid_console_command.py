class InvalidConsoleCommand(Exception):
    """
    Exception for invalid console commands.
    The message should be the usage for that command.
    """

    def __init__(self, message):
        self.message = message
