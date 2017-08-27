#!/usr/bin/python
import shlex
from unidecode import unidecode
from util.loghandler import *
from bottypes.invalid_command import *

"""
	Every handler should initialize the `commands` dictionary with the commands he can handle and the corresponding command class

	The handler factory will then check, if the handler can process a command, resolve it and execute it	
"""	
class HandlerFactory():
	handlers = {}
	
	def registerHandler(handler_name, handler):
		log.info("Registering new handler: %s (%s)" % (handler_name, handler.__class__.__name__))

		HandlerFactory.handlers[handler_name] = handler
		handler.handler_name = handler_name

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

			processMsg = ""
	
			if handler_name in HandlerFactory.handlers:
				# Call a specific handler with this command
				handler = HandlerFactory.getHandler(handler_name)
	
				if (len(args) < 2) or (args[1] == "help"):
					# Generic help handling
					processMsg += handler.getHandlerUsage(slack_client)
					processed = True
				else:
					command = args[1]
						
					if handler.canHandle(command):					
						handler.process(slack_client, command, args[2:], channel, user)
						processed = True
			else:
				# Pass the command to every available handler
				command = args[0]
					
				for handler_name in HandlerFactory.handlers:		
					handler = HandlerFactory.handlers[handler_name]

					if command == "help":						
						processMsg += handler.getHandlerUsage(slack_client)
						processed = True
					elif handler.canHandle(command):						
						handler.process(slack_client, command, args[1:], channel, user)
						processed = True
	
			if not processed:
				msg = "Unknown handler or command : `%s`" % msg
				slack_client.api_call("chat.postMessage", channel=channel, text=msg, as_user=True)

			if processMsg:
				raise InvalidCommand(processMsg)

		except InvalidCommand as e:
			slack_client.api_call("chat.postMessage", channel=channel, text=e.message, as_user=True)
		#except Exception as ex:
		#	log.error("An error has occured while processing a command: %s" % ex)
						