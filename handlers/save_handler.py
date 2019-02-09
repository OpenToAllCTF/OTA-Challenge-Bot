import re

import requests

from bottypes.command_descriptor import *
import handlers.handler_factory as handler_factory
from handlers.base_handler import *
from util.savelinkhelper import unfurl

GITHUB_REPO = ""  # owner/repo-name
GITHUB_BRANCH = ""  # e.g master

CATEGORIES = ["web", "pwn", "re", "crypto", "misc"]


class SaveCommand(Command):
    """Save a url from a slack message according to a specific category"""

    @classmethod
    def execute(cls, slack_wrapper, args, timestamp, channel_id, user_id, user_is_admin):
        """Execute the save link command"""
        if not GITHUB_REPO and not GITHUB_BRANCH:
            raise InvalidCommand("Link saver not configured")
        if args[0] not in CATEGORIES:
            raise InvalidCommand("Invalid Category")

        message = slack_wrapper.get_message(channel_id, timestamp)["messages"][0]["text"]
        url_regex = "((https?):\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?"
        url = re.search(url_regex, message)

        if not url:
            slack_wrapper.post_message(channel_id, "Couldn't extract URL", timestamp)
            return

        url_data = unfurl(url.group())

        data = {
            "fields[title]": url_data["title"],
            "fields[link]": url.group(),
            "fields[description]": url_data["desc"],
            "fields[category]": "{}".format(args[0])
        }
        resp = requests.post(
            "https://dev.staticman.net/v3/entry/github/{}/{}/links".format(
                GITHUB_REPO,
                GITHUB_BRANCH
            ),
            data=data
        ).json()

        if resp["success"]:
            slack_wrapper.post_message(channel_id, "Link saved successfully", timestamp)
        else:
            slack_wrapper.post_message(channel_id, "Error saving the link: `{}`".format(resp), timestamp)


class SaveHandler(BaseHandler):
    """Handler for saving links"""

    def __init__(self):
        self.commands = {
            "link": CommandDesc(
                SaveCommand,
                "Save a link in one of the categories: {}".format(", ".join(CATEGORIES)),
                ["category"], None
            ),
        }


handler_factory.register("save", SaveHandler())
