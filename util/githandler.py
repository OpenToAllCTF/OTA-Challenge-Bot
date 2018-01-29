import os
import json
import datetime
import dulwich
from dulwich import porcelain
from util.loghandler import *

git_config = None
git_support = False

def upload_post(data, post_name, post_directory, commit_message):
    if not git_support:
        raise Exception("Upload post failed: Git support is deactivated...")

    now = datetime.datetime.now()

    post_filename = "{}/{}-{}-{}-{}.md".format(post_directory, now.year, now.month, now.day, post_name)

    try:
        repo_path = git_config["git_repopath"]
        repo_remote = git_config["git_remoteuri"]
        repo_user = git_config["git_repouser"]
        repo_pass = git_config["git_repopass"]
        repo_branch = git_config["git_branch"]

        __git_upload_data(data, repo_path, repo_remote, post_filename,
                          repo_user, repo_pass, repo_branch, commit_message)
    except dulwich.errors.GitProtocolError:
        raise Exception("Upload post failed: GitProtocolError - Check your username and password in the git configuration...")
    except KeyError:
        raise Exception("Upload post failed: KeyError - Check your git configuration for missing keys...")
    except TypeError:
        raise Exception("Upload post failed: TypeError - Did you forget to create a git configuration?")
    except Exception as ex:
        log.exception("upload_post")
        raise Exception("Upload post failed: Unknown - Please check your log files...")


def __git_upload_file(repopath, remotepath, filename, git_username, git_password, git_branch, commit_message):
    repo = porcelain.open_repo(repopath)

    full_filename = os.path.join(repopath, filename)

    porcelain.add(repo, full_filename)
    porcelain.commit(repo, bytes(commit_message, "utf-8"))
    porcelain.push(repo, "https://{}:{}@{}".format(git_username, git_password, remotepath), bytes(git_branch, "utf-8"))


def __git_upload_data(data, repopath, remotepath, filename, git_username, git_password, git_branch, commit_message):
    full_filename = os.path.join(repopath, filename)

    with open(full_filename, "w") as f:
        f.write(data)

    __git_upload_file(repopath, remotepath, filename, git_username, git_password, git_branch, commit_message)


def __init_git_config():
    global git_config, git_support

    try:
        with open("./config_git.json") as f:
            git_config = json.load(f)
        
        git_support=True
    except:
        git_support=False        


__init_git_config()
