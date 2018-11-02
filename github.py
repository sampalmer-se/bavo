import os
import requests


class GitHub(object):

    def __init__(self):
        self.base_url = "https://api.github.com/repos/sampalmer-se/bavo"
        self.token_suffix = "?access_token={}".format(os.environ("GITHUB_TOKEN"))

    def merge_pull_request(self, pull_request_id):
        url = "{}/pulls/{}/merge{}".format(self.base_url, pull_request_id, self.token_suffix)
        data = {
            "merge_method" : "squash"
        }
        requests.put(url, data)

    def merge_master_into_branch(self, branch_name):
        url = "{}/merges{}".format(self.base_url, self.token_suffix)
        data = {
            "base": branch_name,
            "head": "master",
            "commit_message": "Merge master into {}".format(branch_name)
        }
        requests.post(url, json=data)

