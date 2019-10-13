import threading
from abc import ABC, abstractmethod
from util.slack_wrapper import SlackWrapper


class BaseService(ABC):
    """
    Abstract class that every service should inherit from
    """

    def __init__(self, bot_server, slack_wrapper: SlackWrapper):
        self.bot_server = bot_server
        self.slack_wrapper = slack_wrapper
        self.running_thread = None

    @abstractmethod
    def run(self):
        """
        Method called periodically by service handler
        :return: None
        """
        raise NotImplementedError

    @abstractmethod
    def run_time_period(self):
        """
        Method called by service handler to know how often to schedule this service to repeat.
        Give values in seconds.
        :return:
        """
        raise NotImplementedError

    def start(self):
        self.run()
        self.running_thread = threading.Timer(self.run_time_period(), self.start).start()

    def cancel(self):
        self.running_thread.cancel()