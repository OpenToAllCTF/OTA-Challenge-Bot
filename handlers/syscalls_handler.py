#!/usr/bin/env python3
from bottypes.command import *
from bottypes.command_descriptor import *
from bottypes.invalid_command import *
from handlers.handler_factory import *
from handlers.base_handler import *
from addons.syscalls.syscallinfo import *

class ShowAvailableArchCommand(Command):
  """
    Shows the available architecture tables for syscalls
  """
  
  def execute(self, slack_client, args, channel_id, user_id):    
    archList = SyscallsHandler.syscallInfo.getAvailableArchitectures()

    msg = "\n"
    msg += "Available architectures:```"    

    for arch in archList:
      msg += "%s\t" % arch

    msg += "```\n"

    slack_client.api_call("chat.postMessage", channel=channel_id, text=msg.strip(), as_user=True)
  
class ShowSyscallCommand(Command):
  """
    Shows information about the requested syscall
  """

  def sendMessage(self, slack_client, channel, user, msg):
    destChannel = channel if (SyscallsHandler.MSGMODE == 0) else user

    slack_client.api_call("chat.postMessage", channel=destChannel, text=msg.strip(), as_user=True)    

  def parseSyscallInfo(self, syscallEntry):  
    msg = "```"

    for entry in syscallEntry:
      msg += "{0:15} : {1}\n".format(entry, syscallEntry[entry])
  
    return msg.strip() + "```"  

  def execute(self, slack_client, args, channel_id, user_id):    
    archObj = SyscallsHandler.syscallInfo.getArch(args[0])

    if archObj:
      entry = None

      # convenience : Try to search syscall by id or by name, depending on what
      # the user has specified
      try:
        syscallID = int(args[1])
        entry = archObj.getEntryByID(syscallID)
      except:
        entry = archObj.getEntryByName(args[1])

      if entry:        
        self.sendMessage(slack_client, channel_id, user_id, self.parseSyscallInfo(entry))
      else:
        self.sendMessage(slack_client, channel_id, user_id, "Specified syscall not found: `%s (Arch: %s)`" % (args[1], args[0]))
    else:
      self.sendMessage(slack_client, channel_id, user_id, "Specified architecture not available: `%s`" % args[0])

class SyscallsHandler(BaseHandler):
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

  syscallInfo = None

  def __init__(self):
    SyscallsHandler.syscallInfo = SyscallInfo(SyscallsHandler.BASEDIR)

    self.commands = {
        "available" : CommandDesc(ShowAvailableArchCommand, "Shows the available syscall architectures", None, None),
        "show" : CommandDesc(ShowSyscallCommand, "Show information for a specific syscall", ["arch", "syscall name/syscall id"], None),        
    }     

HandlerFactory.registerHandler("syscalls", SyscallsHandler())