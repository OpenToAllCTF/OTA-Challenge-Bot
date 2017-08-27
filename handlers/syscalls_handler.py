#!/usr/bin/env python3
import shlex
import re
import json
import time
from helpers.command import *
from helpers.invalid_command import *
from unidecode import unidecode
from addons.syscalls.syscallinfo import *

def parseSyscallInfo(syscallEntry):  
  msg = "```"

  for entry in syscallEntry:
    msg += "{0:15} : {1}\n".format(entry, syscallEntry[entry])
  
  return msg.strip() + "```"  

class ShowAvailableArchCommand(Command):
  """
    Shows the available architecture tables for syscalls
  """

  def __init__(self, channel, user, syscallInfo):
    self.user = user
    self.syscallInfo = syscallInfo
    self.channel = channel

  def showUsage(self):
    msg  

  def execute(self, slack_client):    
    archList = self.syscallInfo.getAvailableArchitectures()

    msg = "\n"
    msg += "Available architectures:\n"
    msg += "```"

    for arch in archList:
      msg += "%s\t" % arch

    msg += "```\n"

    slack_client.api_call("chat.postMessage",
        channel=self.channel, text=msg.strip(), as_user=True)
  
class ShowSyscallCommand(Command):
  """
    Shows information about the requested syscall
  """

  def __init__(self, args, channel, user, syscallInfo):
    if len(args) < 2:
      raise InvalidCommand("Usage : ```@ota_bot syscalls show <arch> <syscall name / syscall id>```")

    self.user = user
    self.syscallInfo = syscallInfo
    self.channel = channel
    self.args = args

  def sendMessage(self, slack_client, msg):
    destChannel = self.channel if (SyscallsHandler.MSGMODE == 0) else self.user

    slack_client.api_call("chat.postMessage", 
      channel=destChannel, text=msg.strip(), as_user=True)    

  def execute(self, slack_client):
    
    archObj = self.syscallInfo.getArch(self.args[0])

    if archObj:
      entry = None

      # convenience : Try to search syscall by id or by name, depending on what
      # the user has specified
      try:
        syscallID = int(self.args[1])
        entry = archObj.getEntryByID(syscallID)
      except:
        entry = archObj.getEntryByName(self.args[1])

      if entry:
        msg = parseSyscallInfo(entry)
        
        self.sendMessage(slack_client, msg)
      else:
        msg = "Specified syscall not found: `%s (Arch: %s)`" % (self.args[1], self.args[0])

        self.sendMessage(slack_client, msg)
    else:
      msg = "Specified architecture not available: `%s`" % self.args[0]

      self.sendMessage(slack_client, msg)

class SyscallHelpCommand(Command):
    """
      Displays a help menu
    """

    def execute(self, slack_client):
      message = "```"
      message += "@ota_bot syscalls available\n"
      message += "@ota_bot syscalls show <arch> <syscall name/syscall id>\n"
      message += "```"

      raise InvalidCommand(message)


class SyscallsHandler:
  """
    Shows information about syscalls for different architectures.

    Commands :
    # Show available architectures
    @ota_bot syscalls available

    # Show syscall information 
    @ota_bot syscalls show x86 execve
    @ota_bot syscalls show x86 11    
  """

  # Specify the base directory, where the syscall tables are located
  BASEDIR = "addons/syscalls/tables"
  
  # Specify if messages from syscall handler should be posted to channel (0) or per dm (1)
  MSGMODE = 0

  def __init__(self, slack_client):
    self.syscallInfo = SyscallInfo(SyscallsHandler.BASEDIR)

    self.slack_client = slack_client    

  def process(self, command, channel, user):
    try:
      command_line = unidecode(command.lower())
      args = shlex.split(command_line)
      command = None
    except:
      message = "Command failed : Malformed input."
      self.slack_client.api_call("chat.postMessage",
        channel=channel, text=message, as_user=True)
      return

    try:
      # Show available architectures
      if args[:2] == ["syscalls", "available"]:
        command = ShowAvailableArchCommand(channel, user, self.syscallInfo)

      # Show specific syscall
      elif args[:2] == ["syscalls", "show"]:
        command = ShowSyscallCommand(args[2:], channel, user, self.syscallInfo)

      elif args[:1] == ["help"]:
        command = SyscallHelpCommand()

      if command:
        command.execute(self.slack_client)

    except InvalidCommand as e:
      self.slack_client.api_call("chat.postMessage",
        channel=channel, text=e.message, as_user=True)

