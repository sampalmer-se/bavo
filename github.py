import os
import requests


class GitHub(object):

    def __init__(self):
        self.token = os.environ("GITHUB_TOKEN")

    def merge_pull_request(self, pull_request_id):
        url = "https://api.github.com/repos/sampalmer-se/bavo/pulls/{}/merge?access_token={}".format(pull_request_id,
                                                                                                     self.token)
        requests.put(url)
