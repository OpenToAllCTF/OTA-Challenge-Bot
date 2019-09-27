#!/usr/bin/env python3
from util.loghandler import log
from server.botserver import BotServer


if __name__ == "__main__":
    log.info("Initializing threads...")

    server = BotServer()

    server.start()

    # Server should be up and running. Quit when server shuts down
    server.join()

    log.info("Server has shut down. Quit")
