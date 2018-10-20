import requests
import lxml.html
import json
from gettor import db
from gettor.models.models import Show, ShowToTvmaze
import datetime

# DEFAULT_SEARCH_URL = "https://thepiratebay.org/search/"
# DEFAULT_SEARCH_EPILOG = "/0/99/0"
DEFAULT_SEARCH_URL = "https://thepiratebay3.org/index.php?q="
DEFAULT_SEARCH_EPILOG = "&page=0&orderby=99"
DEFAULT_SEARCH_FORMAT = "{0} {1} s{2:02d}e{3:02d}"
# https://thepiratebay3.org/index.php?q=big+bang&page=0&orderby=99

DEFAULT_XPATH_NAME = "//div[@class='detName']/a"
DEFAULT_XPATH_DNL_LNK = "//a[starts-with(@href, 'm')]"
DEFAULT_XPATH_SEED = '//table[@id="searchResult"]//td[3]'
# DEFAULT_XPATH_SEED = "//tr[@class='alt']/td[3]"

empty_url = "", "EMPTY", "", -99


class Downloader():
    def __init__(self):
        self.show = None
        self.search_url = DEFAULT_SEARCH_URL
        self.search_epilog = DEFAULT_SEARCH_EPILOG
        self.xpath_dnl_link = DEFAULT_XPATH_DNL_LNK
        self.xpath_name = DEFAULT_XPATH_NAME
        self.xpath_seed = DEFAULT_XPATH_SEED
        self.html = None
        self.tries = 0
        self.curr_url = None

    def load_show(self, show):
        self.show = show
        self.html = None
        self.tries = 0
        self.curr_url = None

    def construct_search_str(self):
        show_str = DEFAULT_SEARCH_FORMAT.format(self.show.name,
                                                self.show.additional_search,
                                                self.show.season,
                                                self.show.episode)
        url = self.search_url + show_str + self.search_epilog
        return url

    def download_episode(self, next_try=0):
        if self.show is None:
            # TODO change this to exception
            return
        self.tries += next_try
        if self.tries < 0:
            self.tries = 0
        if self.html is None:
            url = self.construct_search_str()
            try:
                response = requests.get(url)
            except (requests.ConnectionError, requests.exceptions.Timeout)as e:
                self.curr_url =  "", str(e), "", -1
                return
            if response.status_code == 200:
                tree = lxml.html.fromstring(response.content)
                self.html = tree
            else:
                # TODO change this to exception
                self.curr_url = "", "Bad Response code (%d)" % response.status_code, "", -2
                return

        dnl_link = self.html.xpath(self.xpath_dnl_link)
        num_links = len(dnl_link)
        dnl_name = "NO NAME"
        dnl_seed = "-1"
        print("dnl: " + str(num_links))
        if num_links <= self.tries:
            self.tries -= next_try
            self.curr_url = "", "NO MORE TORRENTS", "", num_links
            return
        # TODO write how many options for this episode, and if none handle as well
        magnet = dnl_link[self.tries].attrib['href']
        if len(self.html.xpath(self.xpath_name)) > self.tries:
            dnl_name = self.html.xpath(self.xpath_name)[self.tries].text
        if len(self.html.xpath(self.xpath_seed)) > self.tries:
            dnl_seed = self.html.xpath(self.xpath_seed)[self.tries].text

        # TODO get seed number and download name
        print(magnet)
        print(dnl_name)
        print(dnl_seed)
        self.curr_url = magnet, dnl_name, dnl_seed, num_links
        return

    def next_try(self):
        self.tries += 1


class ShowDetails:
    def __init__(self, show):
        self.show = show
        if show.maze_id:
            self.maze_id = show.maze_id
        else:
            query = db.session.query(Show).filter_by(id=show.id).first()
            if query:
                self.maze_id = query.maze_id
            else:
                self.maze_id = None

        if show.link_info:
            self.link = show.link_info + '?embed=episodes'
        else:
            self.link = None
        self.details = None
        self.ep_left = None
        self.ep_details_link = None

    def update_details(self):
        if not self.link:
            return False
        html = requests.get(self.link)
        self.details = json.loads(html.text)
        return True

    def get_episodes_left(self):
        # TODO check when was updated last. if less then an hour no need to update
        if not self.details or not self.details['_embedded']:
            self.ep_left = -1
            return self.ep_left
        cur_ep = self.show.episode
        cur_se = self.show.season
        self.ep_left = 0
        date_now = datetime.datetime.now(datetime.timezone.utc)
        for episode in self.details['_embedded']['episodes']:
            if episode['season'] < cur_se:
                continue
            if episode['season'] == cur_se and episode['number'] < cur_ep:
                continue
            if 'airstamp' in episode:
                t = episode['airstamp']
                tt = datetime.datetime.strptime(''.join(t.rsplit(':', 1)), '%Y-%m-%dT%H:%M:%S%z')
                if date_now > tt:
                    self.ep_left += 1
                else:
                    break
            # TODO else try from other fields
        return self.ep_left

    def get_episode_link(self):
        if not self.details or not self.details['_embedded']:
            self.ep_details_link = None
            return self.ep_details_link
        cur_ep = self.show.episode
        cur_se = self.show.season
        for episode in self.details['_embedded']['episodes']:
            if episode['season'] == cur_se and episode['number'] == cur_ep:
                self.ep_details_link = episode['url']
                return self.ep_details_link
        self.ep_details_link = None
        return self.ep_details_link


