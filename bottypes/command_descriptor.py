#!/usr/bin/env python3
class CommandDesc():
	def __init__(self, command, description, args, optArgs):
		self.command = command
		self.description = description
		self.arguments = args
		self.optionalArgs = optArgs
