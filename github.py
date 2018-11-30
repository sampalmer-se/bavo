import os
import requests
from requests.auth import HTTPBasicAuth


class GitHub(object):

    def __init__(self):
        self.base_url = "https://api.github.com/repos/sampalmer-se/bavo"
        self.jenkins_url = 'http://localhost:8080'
        self.base_cauldron_url = "https://api.github.com/repos/secretescapes/cauldronhackday"
        self.token_suffix = "?access_token={}".format(os.environ.get("GITHUB_TOKEN"))

    def check_branch_exists(self, branch_name):
        url = "{}/branches/{}{}".format(self.base_cauldron_url, branch_name, self.token_suffix)
        response = requests.get(url).json()
        return 'name' in response and response['name'] == branch_name

    def merge_pull_request(self, pull_request_id):
        url = "{}/pulls/{}/merge{}".format(self.base_cauldron_url, pull_request_id, self.token_suffix)
        data = {
            "merge_method": "squash"
        }
        return requests.put(url, json=data)

    def merge_master_into_branch(self, branch_name):
        url = "{}/merges{}".format(self.base_cauldron_url, self.token_suffix)
        data = {
            "base": branch_name,
            "head": "master",
            "commit_message": "Merge master into {}".format(branch_name)
        }
        response = requests.post(url, json=data)
        if response.status_code == 204:
            return {}
        return response.json()

    def get_pull_request_title(self, branch_name):
        url = "{}/pulls{}".format(self.base_cauldron_url, self.token_suffix)
        response_list = requests.get(url).json()
        pr_for_branch = list(filter(lambda pr: pr['head']['ref'] == branch_name, response_list))
        if len(pr_for_branch) == 1:
            return pr_for_branch[0]['title']

        return None

    def trigger_jenkins_test_run(self, row_id, branch_name):
        url = "{}/job/CauldronValidation/buildWithParameters?ROW_ID={}&FRONT_END_BRANCH={}".format(self.jenkins_url,
                                                                                                   row_id, branch_name)
        requests.post(url, auth=HTTPBasicAuth('sam', '8470e4072519928784b04b111a6b3c59'))

    def trigger_jenkins_test_release(self, row_id, version):
        url = "{}/job/CauldronRelease/buildWithParameters?FRONT_END_VERSION={}&ROW_ID={}".format(self.jenkins_url,
                                                                                                 version, row_id)
        requests.post(url, auth=HTTPBasicAuth('sam', '8470e4072519928784b04b111a6b3c59'))
