"""Helper module for uploading solve status posts to SolveTracker repository."""
import json
import datetime
from util.githandler import GitHandler
from util.ctf_template_resolver import resolve_ctf_template, resolve_stats_template
from util.loghandler import log
from bottypes.invalid_command import InvalidCommand

ST_GIT_CONFIG = {}
ST_GIT_SUPPORT = False


def post_ctf_data(ctf, title):
    """Create a post and a statistic file and upload it to the configured SolveTracker repository."""
    if not ST_GIT_SUPPORT:
        raise Exception("Sorry, but the SolveTracker support isn't configured...")

    try:
        now = datetime.datetime.now()

        post_data = resolve_ctf_template(ctf, title, "./templates/post_ctf_template",
                                         "./templates/post_challenge_template")
        post_filename = "_posts/{}-{}-{}-{}.md".format(now.year, now.month, now.day, ctf.name)

        stat_data = resolve_stats_template(ctf)
        stat_filename = "_stats/{}.json".format(ctf.name)

        git = GitHandler(ST_GIT_CONFIG["git_repopath"])

        git.add_file(post_data, post_filename)
        git.add_file(stat_data, stat_filename)

        git.commit("Solve post from {}".format(ctf.name), ST_GIT_CONFIG["git_author"])

        git.push(ST_GIT_CONFIG["git_repouser"], ST_GIT_CONFIG["git_repopass"],
                 ST_GIT_CONFIG["git_remoteuri"], ST_GIT_CONFIG["git_branch"])
    except InvalidCommand as invalid_cmd:
        # Just pass invalid commands on
        raise invalid_cmd
    except Exception:
        log.exception("SolvePostHelper")
        raise InvalidCommand(
            "Something with your configuration files doesn't seem to be correct. Please check your logfiles...")


def init_solvetracker_config():
    """Initialize the SolveTracker configuration or disable SolveTracker support if config file doesn't exist."""
    try:
        with open("./config_solvetracker.json") as f:
            return json.load(f), True
    except:
        log.info("Solvetracker configuration couldn't be loaded. Deactivating SolveTracker...")
        return None, False


ST_GIT_CONFIG, ST_GIT_SUPPORT = init_solvetracker_config()
