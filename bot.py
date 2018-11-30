# -*- coding: utf-8 -*-
"""
Python Slack Bot class for use with the pythOnBoarding app
"""
import os

from slackclient import SlackClient
import sqlite3
from datetime import datetime
import requests


class Bot(object):
    def __init__(self):
        super(Bot, self).__init__()
        self.name = "bavo"
        self.oauth = {"client_id": os.environ.get("CLIENT_ID"),
                      "client_secret": os.environ.get("CLIENT_SECRET"),
                      "scope": "bot"}
        self.dbname = 'bavo.db'

    def add_to_queue(self, user_id, team_id):
        conn = sqlite3.connect(self.dbname)
        conn.cursor().execute("insert into front_end_queue (user_id,team_id, branch_name, cauldron_version) values (?,"
                              "?,?,?)", (user_id, team_id, None, None,))
        conn.commit()
        return self.get_user_from_queue(user_id)

    def update_branch_name(self, user_id, branch_name):
        conn = sqlite3.connect(self.dbname)
        conn.cursor().execute('update front_end_queue set branch_name = ? where user_id = ?', (branch_name, user_id,))
        conn.commit()

    def update_pull_request_id(self, user_id, pull_request_id):
        conn = sqlite3.connect(self.dbname)
        conn.cursor().execute('update front_end_queue set pull_request_id = ? where user_id = ?', (pull_request_id,
                                                                                                   user_id,))
        conn.commit()

    def get_queue_entry_by_row_id(self, row_id):
        conn = sqlite3.connect(self.dbname)
        result = conn.cursor().execute('select pull_request_id, user_id, team_id from front_end_queue where rowid = ?',
                                       (row_id,)).fetchone()
        return {
            'pull_request_id': result[0],
            'user_id': result[1],
            'team_id': result[2]
        }

    @staticmethod
    def get_joke():
        response = requests.get("https://icanhazdadjoke.com/slack")
        return response.json()['attachments'][0]['text']

    def get_current_queue(self):
        conn = sqlite3.connect(self.dbname)
        c = conn.cursor()
        results = c.execute('select rowid, user_id, branch_name, team_id from front_end_queue where added is not null '
                            'order by '
                            'added asc').fetchall()
        return [{
            'user_id': r[1],
            'branch_name': r[2],
            'row_id': r[0],
            'team_id': r[3]
        } for r in results]

    def set_added_timestamp(self, user_id):
        conn = sqlite3.connect(self.dbname)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.cursor().execute('update front_end_queue set added = ? where user_id = ?', (now, user_id,))
        conn.commit()

    def get_user_from_queue(self, user_id):
        conn = sqlite3.connect(self.dbname)
        user_response = conn.cursor().execute('select rowid, * from front_end_queue where user_id = ?', (user_id,)).fetchone()
        if user_response is None:
            return None
        return {
            'row_id': user_response[0],
            'user_id': user_response[1],
            'team_id': user_response[2],
            'branch_name': user_response[3],
            'pull_request_id': user_response[4],
            'cauldron_version': user_response[5],
        }

    def get_slack_client(self, team_id):
        conn = sqlite3.connect(self.dbname)
        token = conn.cursor().execute('select token from authed_teams where team_id = ?', (team_id,)).fetchone()[0]
        return SlackClient(token)

    def auth(self, code):
        response = SlackClient("").api_call(
            "oauth.access",
            client_id=self.oauth["client_id"],
            client_secret=self.oauth["client_secret"],
            code=code
        )

        team_id = response["team_id"]
        conn = sqlite3.connect(self.dbname)
        conn.cursor().execute('insert into authed_teams (team_id, token) values (?,?) on conflict(team_id) do '
                              'update set token = excluded.token', (team_id, response["bot"]["bot_access_token"],))
        conn.commit()

    def open_dm(self, user_id, team_id):
        new_dm = self.get_slack_client(team_id).api_call("im.open",
                                                         user=user_id)
        dm_id = new_dm["channel"]["id"]
        return dm_id

    def send_message(self, team_id, user_id, text):
        # Then we'll set that message object's channel attribute to the DM
        # of the user we'll communicate with
        channel = self.open_dm(user_id, team_id)

        self.get_slack_client(team_id).api_call("chat.postMessage",
                                                channel=channel,
                                                username=self.name,
                                                text=text,
                                                )

    def remove_from_queue(self, row_id):
        conn = sqlite3.connect(self.dbname)
        conn.cursor().execute('delete from front_end_queue where rowid = ?', (row_id,))
        conn.commit()

    def delete_user_from_queue(self, user_id):
        conn = sqlite3.connect(self.dbname)
        queue = conn.cursor().execute('select rowid from front_end_queue where user_id = ? order by added desc limit 1',
                              (user_id,)).fetchone()
        if queue is None:
            return False

        self.remove_from_queue(queue[0])
        return True
