#!/usr/bin/env python3

class Challenge:
  def __init__(self, channel_id, name):
    """
      An object representation of an ongoing challenge.
      channel_id : The slack id for the associated channel
      name : The name of the challenge
    """

    self.channel_id = channel_id
    self.name = name
    self.is_solved = False
    self.solver = None

  def mark_as_solved(self, user_id):
    """
      Mark a challenge as solved.
      user_id : The slack user identifier for the solver.
    """
    self.is_solved = True
    self.solver = user_id

  def unmark_as_solved(self):
    """
      Unmark a challenge as solved.
    """
    self.is_solved = False
    self.solver = None
