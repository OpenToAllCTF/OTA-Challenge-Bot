"""GitHandler module - Provides GitHandler with shortcuts for handling git repository access."""
import os
import dulwich

from dulwich import porcelain
from util.loghandler import log
from bottypes.invalid_command import InvalidCommand


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
            porcelain.push(self.repo, "https://{}:{}@{}".format(repo_user,
                                                                repo_pass, repo_remote), bytes(repo_branch, "utf-8"))
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
