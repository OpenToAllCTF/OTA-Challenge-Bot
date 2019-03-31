"""Helper module for save_handler to fetch details of a url."""
import re
import json

import requests
from bs4 import BeautifulSoup

from util.loghandler import log


def get_title(soup: BeautifulSoup):
    title = soup.find("meta", property=re.compile("title", re.I)) or \
        soup.find("meta", attrs={"name": re.compile("title", re.I)})
    if title:
        title = title["content"]
    else:
        title = soup.title.string

    title = title.replace("|", "-")
    return title.strip()


def get_desc(soup: BeautifulSoup):
    desc = soup.find("meta", property=re.compile("desc", re.I)) or \
        soup.find("meta", attrs={"name": re.compile("desc", re.I)})
    if desc:
        return desc["content"].strip()

    return ""


def get_content(url: str):
    resp = requests.get("https://urlembed.com/json/url/{}".format(url))
    if not resp.ok:
        return "", ""
    resp = resp.json()
    content = BeautifulSoup(resp["content"], "html.parser").prettify()
    return content, resp["url"]  # resp["url"] is image's URL


def unfurl(url: str):
    resp = requests.get(url).text
    soup = BeautifulSoup(resp, "html.parser")
    content, img = get_content(url)

    details = {
        "title": get_title(soup),
        "desc": get_desc(soup),
        "content": content,
        "img": img
    }

    return details


def init_savelink_config():
    """Initialize the Save handler configuration"""
    try:
        with open("./config_savelink.json") as f:
            conf = json.load(f)
            return conf, True
    except (IOError, FileNotFoundError) as e:
        log.info("Save handler configuration couldn't be loaded: %s.", e)
        return None, False


LINKSAVE_CONFIG, LINKSAVE_SUPPORT = init_savelink_config()
