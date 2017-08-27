#!/usr/bin/python3
from slackclient import SlackClient
from util.loghandler import *
from util.util import *
import json
import threading
import time

"""
	This should also be refactored to a "ConsoleHandler" and work with Commands like the BotHandlers.
	Would make a much cleaner design, than using if/else
"""
class ConsoleThread(threading.Thread):	
	def __init__(self, botserver):		
		self.botserver = botserver
		threading.Thread.__init__(self)
	
	def run(self):
		self.running = True

		while True:
			try:
				inputMsg = input("")

				print ("Command : %s" % inputMsg)

				parts = inputMsg.split(" ")

				cmd = parts[0].lower()

				if cmd == "quit":
					self.botserver.quit()
					break

				# Example command: Useless, but just an example, for what console handler could do
				elif cmd == "createchannel":
					if len(parts)<2:
						print ("Usage: createchannel <channel>")
					else:					
						create_channel(self.botserver.slack_client, parts[1])
			except:
				print ("Error at executing command...")
