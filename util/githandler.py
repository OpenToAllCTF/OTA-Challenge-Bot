"""GitHandler module - Provides GitHandler with shortcuts for handling git repository access."""
import os
import re
from io import StringIO

import dulwich
from dulwich import porcelain

from bottypes.invalid_command import InvalidCommand
from util.loghandler import log


class GitHandler():
    """Handles commit for multiple files."""

    def __init__(self, repo_path):
        try:
            self.repo_path = repo_path

            self.repo = porcelain.open_repo(repo_path)
        except Exception:
            log.exception("GitHandler::__init__()")
            raise InvalidCommand("Opening repo failed: Please check your log")

    def add_file(self, data, filename):
        """Add a file to the commit."""
        try:
            full_filename = os.path.join(self.repo_path, filename)

            with open(full_filename, "w") as f:
                f.write(data)

            porcelain.add(self.repo, full_filename)
        except Exception:
            # Anonymizing exceptions
            log.exception("GitHandler::add_file()")
            raise InvalidCommand("Adding file failed: Please check your log files...")

    def commit(self, commit_message):
        """Commit the current changeset."""
        try:
            porcelain.commit(self.repo, bytes(commit_message, "utf-8"))
        except Exception:
            # Anonymizing exceptions
            log.exception("GitHandler::commit()")
            raise InvalidCommand("Comitting file failed: Please check your log files...")

    def push(self, repo_user, repo_pass, repo_remote, repo_branch):
        """Push the current commit to git."""
        try:
            if repo_pass:
                porcelain.push(self.repo,
                        "https://{}:{}@{}".format(repo_user, repo_pass, repo_remote),
                        bytes(repo_branch, "utf-8"))
            else:
                porcelain.push(self.repo, 
                        "git@{}".format(repo_remote), 
                        bytes(repo_branch, "utf-8"))

        except dulwich.errors.GitProtocolError:
            raise InvalidCommand(
                "Upload file failed: GitProtocolError - Check your username and password in the git configuration...")
        except KeyError:
            raise InvalidCommand("Upload file failed: KeyError - Check your git configuration for missing keys...")
        except TypeError:
            raise InvalidCommand("Upload file failed: TypeError - Did you forget to create a git configuration?")
        except Exception:
            log.exception("GitHandler::push()")
            raise InvalidCommand("Upload file failed: Unknown - Please check your log files...")

    def get_version(self):
        last_log = StringIO()

        # Get current branch
        current_branch = self.repo.refs.follow(b"HEAD")[0][1].decode().split("/")[-1]

        # Get last commit
        porcelain.log(self.repo, outstream=last_log, max_entries=1)

        commit_msg = last_log.getvalue()

        commit_match = re.search('commit: (.+?)\n', commit_msg)
        commit = commit_match.group(1) if commit_match else ""

        commit_match = re.search('Date: (.+?)\n\n', commit_msg)
        commit_date = commit_match.group(1).strip() if commit_match else ""

        commit_match = re.search("\n\n(.+?)\Z", commit_msg, flags=re.DOTALL)
        commit_info = commit_match.group(1).strip() if commit_match else ""

        return "I'm running commit `{}` of branch `{}`\n\n*{}*```{}```".format(commit, current_branch, commit_date, commit_info)
