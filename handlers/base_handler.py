#!/usr/bin/python3
from abc import ABC, abstractmethod
from bottypes.command import *
from bottypes.invalid_command import *

class BaseHandler(ABC):
	def canHandle(self, command):    
		if command in self.commands:      
			return True

		return False

	def init(self, slack_client, botid):
		pass

	def showUsage(self, slack_client):
		pass

	def process(self, slack_client, command, args, channel, user):    
		try:            
			self.commands[command]().execute(slack_client, args, channel, user)
		except InvalidCommand as e:
			slack_client.api_call("chat.postMessage", channel=channel, text=e.message, as_user=True)
