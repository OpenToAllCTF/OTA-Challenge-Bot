import json
import threading
import time
from util.loghandler import *
from util.util import *
from bottypes.invalid_console_command import *

# This should also be refactored to a "ConsoleHandler" and work with Commands like the BotHandlers.
# Would make a much cleaner design, than using if/else


class ConsoleThread(threading.Thread):

    def __init__(self, botserver):
        self.botserver = botserver
        threading.Thread.__init__(self)

    def update_config(self, option, value):
        try:
            self.botserver.set_config_option(option, value)
        except InvalidConsoleCommand as e:
            log.error(e.message)

    def show_set_usage(self):
        print("\nUsage: set <option> <value>")
        print("")
        print("Available options:")

        if self.botserver.config:
            for config_option in self.botserver.config:
                print("{0:20} = {1}".format(config_option,
                                            self.botserver.config[config_option]))
        print("")

    def quit(self):
        """Inform the application that it is quitting."""
        log.info("Shutting down")
        self.running = False

    def run(self):
        self.running = True

        while self.running:
            try:
                parts = input("").split(" ")

                cmd = parts[0].lower()

                if cmd == "quit":
                    self.botserver.quit()
                    break

                # Example command: Useless, but just an example, for what
                # console handler could do
                elif cmd == "createchannel":
                    if len(parts) < 2:
                        print("Usage: createchannel <channel>")
                    else:
                        self.botserver.slack_wrapper.create_channel(parts[1])
                elif cmd == "set":
                    if len(parts) < 3:
                        self.show_set_usage()
                    else:
                        self.update_config(parts[1], parts[2])
            except Exception:
                log.exception(
                    "An error has occured while processing a console command")
