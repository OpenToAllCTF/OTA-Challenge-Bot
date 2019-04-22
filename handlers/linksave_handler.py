import re

import requests

from bottypes.command import Command
from bottypes.command_descriptor import CommandDesc
from bottypes.invalid_command import InvalidCommand
from handlers import handler_factory
from handlers.base_handler import BaseHandler
from util.loghandler import log
from util.savelinkhelper import LINKSAVE_CONFIG, LINKSAVE_SUPPORT, unfurl

CATEGORIES = ["web", "pwn", "re", "crypto", "misc"]


class SaveLinkCommand(Command):
    """Save a url from a slack message according to a specific category."""

    @classmethod
    def execute(cls, slack_wrapper, args, timestamp, channel_id, user_id, user_is_admin):
        """Execute the save command."""

        if not LINKSAVE_SUPPORT:
            raise InvalidCommand("Save Link failed: Link saver not configured.")
        if args[0] not in CATEGORIES:
            raise InvalidCommand("Save Link failed: Invalid Category.")
        if LINKSAVE_CONFIG["allowed_users"] and user_id not in LINKSAVE_CONFIG["allowed_users"]:
            raise InvalidCommand("Save Link failed: User not allowed to save links")

        message = slack_wrapper.get_message(channel_id, timestamp)["messages"][0]["text"]
        profile_details = slack_wrapper.get_member(user_id)["user"]["profile"]
        url_regex = "((https?):\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?"
        url = re.search(url_regex, message)

        if not url:
            slack_wrapper.post_message(channel_id, "Save Link failed: Unable to extract URL", timestamp)
            return

        try:
            url_data = unfurl(url.group())
        except requests.exceptions.Timeout as e:
            slack_wrapper.post_message(channel_id, "Save Link failed: Request timed out", timestamp)
            log.error(e)
            return

        data = {
            "options[staticman-token]": LINKSAVE_CONFIG["staticman-token"],
            "fields[title]": url_data["title"],
            "fields[link]": url.group(),
            "fields[excerpt]": url_data["desc"],
            "fields[category]": args[0],
            "fields[header][overlay_image]": url_data["img"],
            "fields[user]": profile_details["display_name"] or profile_details["real_name"]
        }
        resp = requests.post(
            "https://mystaticmanapp.herokuapp.com/v2/entry/{git_repo}/{git_branch}/links".format_map(
                LINKSAVE_CONFIG
            ),
            data=data
        ).json()

        if resp["success"]:
            slack_wrapper.post_message(channel_id, "Link saved successfully", timestamp)
        else:
            slack_wrapper.post_message(channel_id, "Error saving the link", timestamp)
            log.error(resp)


class ShowLinkSaveURLCommand(Command):
    """Show the url for the link saver repo."""

    @classmethod
    def execute(cls, slack_wrapper, args, timestamp, channel_id, user_id, user_is_admin):
        url = LINKSAVE_CONFIG["repo_link_url"]

        if not url:
            raise InvalidCommand("Link saver: URL for link repository not configured.")

        slack_wrapper.post_message(channel_id, "Link saver: {}".format(url))


class LinkSaveHandler(BaseHandler):
    """Handler for saving links."""

    def __init__(self):
        if LINKSAVE_SUPPORT:
            self.commands = {
                "link": CommandDesc(SaveLinkCommand, "Save a link in one of the categories: {}".format(", ".join(CATEGORIES)), ["category"], None),
                "showlinkurl": CommandDesc(ShowLinkSaveURLCommand, "Show the url for linksaver repo", None, None)
            }


handler_factory.register("linksave", LinkSaveHandler())
