# coding=utf-8
import datetime

import requests
from slackclient import SlackClient
from bs4 import BeautifulSoup
from services.base_service import BaseService
from util.loghandler import log
from util.slack_wrapper import SlackWrapper
import time
import os


class RankService(BaseService):
    """
    Service to periodically check ctftime rank, and post any updates
    """

    def run_time_period(self):
        return 60 * 60  # Hourly

    def __init__(self, botserver, slack_wrapper: SlackWrapper):
        super().__init__(botserver, slack_wrapper)
        self.lookup_add = ""
        self.add_id = 1

        self.team_name = u"the cr0wn"
        self.slack_token = botserver.get_config_option("api_key")
        self.position_filename = "old-pos.txt"
        self.post_channel_id = self.find_channel_id("general")

    def find_channel_id(self, channel_name):
        x = self.slack_wrapper.get_public_channels()

        channels = x["channels"]
        for channel in channels:
            if channel["name"] == channel_name:
                return channel["id"]
        raise ValueError("Channel not found!")

    def run(self):
        position_found = None
        old_position = -1

        position_changed = False
        points_found = -1

        while position_found is None and self.add_id < 100:
            quote_page = 'https://ctftime.org/stats/{}'.format(self.lookup_add)
            # This useragent needs to be randomish otherwise we get 403'd
            page = requests.get(quote_page, headers={'User-Agent': "Otters inc."})
            soup = BeautifulSoup(page.text, 'html.parser')

            data = []
            table = soup.find('table', attrs={'class': 'table table-striped'})

            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                cols = [ele.text.strip() for ele in cols]
                data.append([ele for ele in cols if ele])

            if os.path.isfile(self.position_filename):
                with open(self.position_filename, 'r') as f:
                    old_position = int(f.read().replace('\n', ''))

            for l in data:
                if len(l) > 1 and l[1] == self.team_name:
                    position_found = int(l[0])
                    points_found = float(l[2])

            if not position_found:
                self.add_id += 1
            self.lookup_add = "2019?page={}".format(self.add_id)

        if position_found is None:
            log.error("Cannot find position in first 100 pages!")
            return

        if old_position != position_found:
            position_changed = True

        with open(self.position_filename, "w") as f:
            f.write(str(position_found))

        ts = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

        if not position_changed:
            log.info("{} : Nothing changed, staying quiet".format(ts))
            return

        message = u"*------- 🚨 CTFTIME ALERT 🚨 -------*\n\n@channel\n" \
                  "*We moved from position {} to {} in the world! 🌍🌍🌍🌍🌍" \
                  "*\n\n*We have {} points*\n\n" \
                  "https://ctftime.org/stats/{}".format(old_position, position_found, points_found, self.lookup_add)

        self.slack_wrapper.post_message(self.post_channel_id, message)
        log.info("{} : sent update".format(ts))