#!/usr/bin/python
from util.loghandler import *
import shlex
from unidecode import unidecode

"""
	Every handler should initialize the `commands` dictionary with the commands he can handle and the corresponding command class

	The handler factory will then check, if the handler can process a command, resolve it and execute it	
"""	
class HandlerFactory():
	handlers = {}
	
	def registerHandler(handler_name, handler):
		log.info("Registering new handler: %s (%s)" % (handler_name, handler.__class__.__name__))

		HandlerFactory.handlers[handler_name] = handler

	"""
		Initializes all handler with common information.

		Might remove bot_id from here later on?
	"""
	def initializeHandlers(slack_client, bot_id):
		for handler in HandlerFactory.handlers:
			HandlerFactory.handlers[handler].init(slack_client, bot_id)

	def getHandler(handler_name):
		if handler_name in HandlerFactory.handlers:
			return HandlerFactory.handlers[handler_name]

		return None

	def process(slack_client, msg, channel, user):
		log.debug("Processing message: %s from %s (%s)" % (msg, channel, user))

		try:
			command_line = unidecode(msg.lower())
			args = shlex.split(command_line)
		except:      		
			message = "Command failed : Malformed input."
			slack_client.api_call("chat.postMessage", channel=channel, text=message, as_user=True)
			return

		try:
			handler_name = args[0]
	
			processed = False
	
			if handler_name in HandlerFactory.handlers:
				# Call a specific handler with this command
				handler = HandlerFactory.getHandler(handler_name)
	
				if len(args) < 2:
					# Try to call help command for specified handler				
					handler.process(slack_client, "help", "", channel, user)
					processed = True
				else:
					command = args[1]
	
					if handler.canHandle(command):					
						handler.process(slack_client, command, args[2:], channel, user)
						processed = True
			else:
				# Pass the command to every available handler
				command = args[0]
					
				for handler in HandlerFactory.handlers.values():		
					if handler.canHandle(command):
						processed = True
						handler.process(slack_client, command, args[1:], channel, user)
	
			if not processed:
				msg = "Unknown handler or command : `%s`" % msg
				slack_client.api_call("chat.postMessage", channel=channel, text=msg, as_user=True)
		except Exception as ex:
			log.error("An error has occured while processing a command: %s" % ex)
						