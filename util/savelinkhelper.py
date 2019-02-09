"""Helper module for save_handler to fetch details of a url."""
import re
import requests
from bs4 import BeautifulSoup


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
    else:
        return ""


def unfurl(url: str):
    details = {}
    resp = requests.get(url).text
    soup = BeautifulSoup(resp, "html.parser")
    details["title"] = get_title(soup)
    details["desc"] = get_desc(soup)
    return details
