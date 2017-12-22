import threading
import time
import queue
from util.loghandler import log


class MessageQueue(threading.Thread):
    def __init__(self, slack_wrapper, use_queue=True, queue_interval=5):
        self.slack_wrapper = slack_wrapper
        self.use_queue = use_queue
        self.queue_interval = queue_interval
        self.message_queue = queue.Queue()
        self.is_running = True

        threading.Thread.__init__(self)
        self.thread_lock = threading.Lock()

    def stop(self):
        self.lock()
        self.is_running = False
        self.release()

    def lock(self):
        """Acquire global lock for working with (not thread-safe) data."""
        self.thread_lock.acquire()

    def release(self):
        """Release global lock after accessing (not thread-safe) data."""
        self.thread_lock.release()

    def add_message(self, msg):
        """
        Add a message to the message queue.

        Args:
            msg(obj): The message entry object to put into the queue.
        """
        if self.use_queue:
            self.lock()
            self.message_queue.put(msg)
            self.release()
        else:
            self.slack_wrapper.post_message(msg.channel_id, msg.get_formatted_message())


    def run(self):
        log.info("Message queue started.")

        while self.is_running:
            time.sleep(self.queue_interval)

            self.lock()

            if not self.message_queue.empty():
                message_dict = {}

                # Group messages per channel
                while not self.message_queue.empty():
                    msg = self.message_queue.get()

                    if msg.channel_id not in message_dict:
                        message_dict[msg.channel_id] = ""

                    message_dict[msg.channel_id] += "{}\n".format(msg.get_formatted_message())

                # Post queued messages per channel (if overused, this could hit rate-limit)
                # TODO: Define a maximum channel count per dequeue phase
                for queue_channel in message_dict:
                    self.slack_wrapper.post_message(queue_channel, message_dict[queue_channel])

            self.release()

        log.info("Message queue thread ended gracefully.")
