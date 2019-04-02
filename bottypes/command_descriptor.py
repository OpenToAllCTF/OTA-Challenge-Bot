class CommandDesc():

    def __init__(self, command, description, args=None, opt_args=None, is_admin_cmd=False):
        self.command = command
        self.description = description
        self.arguments = args or []
        self.opt_arguments = opt_args or []
        self.is_admin_cmd = is_admin_cmd
