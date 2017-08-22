#!/usr/bin/env python3

class Command:
  """
    The command interface to be used
  """
  def __init__(self, args, user): pass
  def execute(self, slack_client): pass
