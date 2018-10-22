from datetime import datetime
from gettor import db
import os
import json
import requests


def download_image(url, pic_target):
    if os.path.isfile(pic_target):
        print("pictures exists")
        return True
    head, tail = os.path.split(pic_target)
    if not os.path.isdir(head):
        os.mkdir(head)
    response = requests.get(url)
    if response.status_code == 200:
        with open(pic_target, 'wb') as f:
            f.write(response.content)
    else:
        return False
    del response
    return True


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_trainer = db.Column(db.Boolean, default=False)
    email = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return '<User %r (trainer: %s>' % (self.username, str(self.is_trainer))

    def __init__(self, username=None, password=None, is_trainer=False, email=None):
        self.username = username
        self.password = password
        self.is_trainer = is_trainer
        self.email = email


class Show(db.Model):
    __tablename__ = 'shows'
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    additional_search = db.Column(db.String(120), nullable=False)
    link_info = db.Column(db.String(120))
    link_pic = db.Column(db.String(120))
    link_details = db.Column(db.String(120))
    season = db.Column(db.Integer, nullable=False)
    episode = db.Column(db.Integer, nullable=False)
    maze_id = db.Column(db.Integer)

    def __repr__(self):
        return '<show %s, season %d, episode %d>' % (self.name, self.season, self.episode)

    def __init__(self, author_id=None, name=None, additional_search="", season=None, episode=None, link_info=""):
        self.author_id = author_id
        self.name = name
        self.additional_search = additional_search
        self.season = season
        self.episode = episode
        self.link_info = link_info
        self.show_details = None

    def get_maze_link(self):
        if self.link_info:
            return 0

        html = requests.get("http://api.tvmaze.com/singlesearch/shows?q=" + self.name + "&embed=episodes")
        details = json.loads(html.text)
        self.link_info = details['_links']['self']['href']
        if 'image' in details and 'medium' in details['image']:
            self.link_pic = details['image']['medium']
        else:
            self.link_pic = ""
        self.maze_id = details['id']
        self.link_details = details['url']
        return details['id']

    def step(self):
        if self.show_details:
            se, ep = self.show_details.get_next_episode()
            self.season = se
            self.episode = ep
        else:
            self.episode += 1
        # TODO check if season is over so step to next season


class ShowToTvmaze(db.Model):
    __tablename__ = 'shows_to_tvmaze'
    id = db.Column(db.Integer, primary_key=True)
    maze_id = db.Column(db.Integer, nullable=False)
    show_id = db.Column(db.Integer, db.ForeignKey('shows.id'), nullable=False)

    def __repr__(self):
        return '<id %d: maze id %d, show id %d>' % (self.id, self.maze_id, self.show_id)

    def __init__(self, maze_id, show_id):
        self.maze_id = maze_id
        self.show_id = show_id
