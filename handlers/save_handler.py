import re

import requests

from bottypes.command_descriptor import *
import handlers.handler_factory as handler_factory
from handlers.base_handler import *
from util.savelinkhelper import unfurl, SAVE_CONFIG, SAVE_SUPPORT
from util.loghandler import log

CATEGORIES = ["web", "pwn", "re", "crypto", "misc"]


class SaveCommand(Command):
    """Save a url from a slack message according to a specific category."""

    @classmethod
    def execute(cls, slack_wrapper, args, timestamp, channel_id, user_id, user_is_admin):
        """Execute the save command."""

        if not SAVE_SUPPORT:
            raise InvalidCommand("Link saver not configured.")
        if args[0] not in CATEGORIES:
            raise InvalidCommand("Invalid Category.")

        message = slack_wrapper.get_message(channel_id, timestamp)["messages"][0]["text"]
        profile_details = slack_wrapper.get_member(user_id)["user"]["profile"]
        url_regex = "((https?):\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?"
        url = re.search(url_regex, message)

        if not url:
            slack_wrapper.post_message(channel_id, "Error: `Unable to extract URL`", timestamp)
            return

        url_data = unfurl(url.group())

        data = {
            "options[staticman-token]": SAVE_CONFIG["staticman-token"],
            "fields[title]": url_data["title"],
            "fields[link]": url.group(),
            "fields[excerpt]": url_data["desc"],
            "fields[category]": args[0],
            "fields[content]": url_data["content"],
            "fields[header][overlay_image]": url_data["img"],
            "fields[user]": profile_details["display_name"] or profile_details["real_name"]
        }
        resp = requests.post(
            "https://mystaticmanapp.herokuapp.com/v2/entry/{git_repo}/{git_branch}/links".format_map(
                SAVE_CONFIG
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
