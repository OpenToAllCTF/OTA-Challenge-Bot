#!/usr/bin/python3
from util.loghandler import *
from server.botserver import *
from server.consolethread import *

if __name__  == "__main__":
    log.info("Initializing threads...")

    server = BotServer()
    server.start()

    console = ConsoleThread(server)
    console.start()

    # Server should be up and running. Quit when server shuts down
    server.join()

    log.info("Server has shut down. Quit")
