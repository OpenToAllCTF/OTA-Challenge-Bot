import re

import requests

from bottypes.command_descriptor import *
import handlers.handler_factory as handler_factory
from handlers.base_handler import *
from util.savelinkhelper import unfurl, GITHUB_BRANCH, GITHUB_REPO
from util.loghandler import log

CATEGORIES = ["web", "pwn", "re", "crypto", "misc"]


class SaveCommand(Command):
    """Save a url from a slack message according to a specific category."""

    @classmethod
    def execute(cls, slack_wrapper, args, timestamp, channel_id, user_id, user_is_admin):
        """Execute the save command."""

        if not GITHUB_REPO or not GITHUB_BRANCH:
            raise InvalidCommand("Link saver not configured.")
        if args[0] not in CATEGORIES:
            raise InvalidCommand("Invalid Category.")

        message = slack_wrapper.get_message(channel_id, timestamp)["messages"][0]["text"]
        url_regex = "((https?):\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?"
        url = re.search(url_regex, message)

        if not url:
            slack_wrapper.post_message(channel_id, "Error: `Unable to extract URL`", timestamp)
            return

        url_data = unfurl(url.group())

        data = {
            "fields[title]": url_data["title"],
            "fields[link]": url.group(),
            "fields[excerpt]": url_data["desc"],
            "fields[category]": args[0],

            # https://github.com/eduardoboucas/staticman/issues/267
            "fields[content]": "{} ...".format(url_data["content"][:10000]),

            "fields[header][overlay_image]": url_data["img"]
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
            slack_wrapper.post_message(channel_id, "Error saving the link", timestamp)
            log.error(resp)


class SaveHandler(BaseHandler):
    """Handler for saving links."""

    def __init__(self):
        self.commands = {
            "link": CommandDesc(
                SaveCommand,
                "Save a link in one of the categories: {}".format(", ".join(CATEGORIES)),
                ["category"], None
            ),
        }


handler_factory.register("save", SaveHandler())
