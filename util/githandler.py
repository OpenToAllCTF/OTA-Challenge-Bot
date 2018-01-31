import os
import json
import dulwich
from dulwich import porcelain
from util.loghandler import log

GIT_CONFIG = None
GIT_SUPPORT = False


class GitCheckin():
    """Handles commit for multiple files."""

    def __init__(self):
        if not GIT_SUPPORT:
            raise Exception("Upload post failed: Git support is deactivated...")

        self.repo_path = GIT_CONFIG["git_repopath"]
        self.repo_remote = GIT_CONFIG["git_remoteuri"]
        self.repo_user = GIT_CONFIG["git_repouser"]
        self.repo_pass = GIT_CONFIG["git_repopass"]
        self.repo_branch = GIT_CONFIG["git_branch"]

        self.repo = porcelain.open_repo(self.repo_path)

    def add_file(self, data, filename):
        """Add a file to the commit."""
        try:
            full_filename = os.path.join(self.repo_path, filename)

            with open(full_filename, "w") as f:
                f.write(data)

            porcelain.add(self.repo, full_filename)
        except Exception:
            # Anonymizing exceptions
            raise Exception("Adding file failed: Please check your log files...")

    def commit(self, commit_message):
        """Commit the current changeset."""
        try:
            porcelain.commit(self.repo, bytes(commit_message, "utf-8"))
        except Exception:
            # Anonymizing exceptions
            raise Exception("Comitting file failed: Please check your log files...")

    def push(self):
        """Push the current commit to git."""
        try:
            porcelain.push(self.repo, "https://{}:{}@{}".format(self.repo_user,
                                                                self.repo_pass, self.repo_remote), bytes(self.repo_branch, "utf-8"))
        except dulwich.errors.GitProtocolError:
            raise Exception(
                "Upload post failed: GitProtocolError - Check your username and password in the git configuration...")
        except KeyError:
            raise Exception("Upload post failed: KeyError - Check your git configuration for missing keys...")
        except TypeError:
            raise Exception("Upload post failed: TypeError - Did you forget to create a git configuration?")
        except Exception:
            log.exception("upload_post")
            raise Exception("Upload post failed: Unknown - Please check your log files...")


def __init_git_config():
    global GIT_CONFIG, GIT_SUPPORT

    try:
        with open("./config_git.json") as f:
            GIT_CONFIG = json.load(f)

        GIT_SUPPORT = True
    except:
        GIT_SUPPORT = False


__init_git_config()
