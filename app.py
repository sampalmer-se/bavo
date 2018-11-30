# -*- coding: utf-8 -*-

import json
import bot
import github
import re
from flask import Flask, request, make_response, render_template
# from apscheduler.schedulers.background import BackgroundScheduler
pyBot = bot.Bot()
github = github.GitHub()

app = Flask(__name__)

message_ids = {}


def job():
    print('Hello')


# scheduler = BackgroundScheduler()
# scheduler.add_job(func=job, trigger="interval", seconds=3)
# scheduler.start()


def _event_handler(event_type, slack_event):
    if event_type == "message" and "event" in slack_event and "user" in slack_event["event"]:
        print(json.dumps(slack_event))
        team_id = slack_event['team_id']
        user_id = slack_event['event']['user']
        client_message_id = slack_event['event']['client_msg_id']
        if user_id not in message_ids:
            message_ids[user_id] = []
        if client_message_id not in message_ids[user_id]:
            message_ids[user_id].append(client_message_id)

            current_user = pyBot.get_user_from_queue(user_id)
            text = slack_event['event']['text']

            if 'abort' in text or 'cancel' in text:
                success_delete = pyBot.delete_user_from_queue(user_id)
                if success_delete:
                    pyBot.send_message(team_id, user_id, "I've removed you from the queue \n")
                else:
                    pyBot.send_message(team_id, user_id, "You're not in the queue \n")
                return

            elif 'joke' in text:
                joke = pyBot.get_joke()
                pyBot.send_message(team_id, user_id, joke)

            elif 'hello' in text:
                pyBot.send_message(team_id, user_id, "Hello, I'm Bavo, the patron saint of Falconry :falcon: \n"
                                                     "This is the current queue")
                current_queue = pyBot.get_current_queue()
                pyBot.send_message(team_id, user_id,
                                   '\n'.join(['{}. <@{}>'.format(r['row_id'], r['user_id']) for r in
                                              current_queue]))

            if 'release' in text or 'queue' in text:
                if current_user is None:
                    pyBot.send_message(team_id, user_id, 'Welcome  to the release queue :cauldron:')
                    pyBot.add_to_queue(user_id=user_id, team_id=team_id)
                    pyBot.send_message(team_id, user_id, 'Which branch do you want to release?')

            if current_user is not None:
                if current_user['branch_name'] is None and ' ' not in text:
                    branch_exists = github.check_branch_exists(text)
                    if branch_exists:
                        pyBot.update_branch_name(user_id, text)
                        pyBot.set_added_timestamp(user_id)
                        pyBot.send_message(team_id, user_id, "Ok I've found the branch :thumbsup:")

                        title = github.get_pull_request_title(text)

                        if title is not None:
                            pyBot.update_pull_request_id(user_id, text)
                            pyBot.send_message(team_id, user_id,
                                               "I've found a pull request with title *{}* and added you to the queue. "
                                               "Here is the current queue".format(title))
                            current_queue = pyBot.get_current_queue()
                            pyBot.send_message(team_id, user_id,
                                               '\n'.join(['{}. <@{}>'.format(r['row_id'], r['user_id']) for r in
                                                          current_queue]))
                            if len(current_queue) == 1:
                                first_item = current_queue[0]
                                release(first_item['user_id'], team_id, first_item['branch_name'], first_item['row_id'])
                        else:
                            pyBot.send_message(team_id, user_id, "I can't find a pull request for this branch :cry:".format(text))
                    else:
                        pyBot.send_message(team_id, user_id, "I can't find branch {}".format(text))

                if current_user['cauldron_version'] is None and re.search(r'[vV]\d*', text) is not None:
                    version = re.search(r'[vV]\d*', text)
                    github.trigger_jenkins_test_release(current_user['row_id'], version)

        else:
            return


def is_number(value):
    try:
        int(value)
    except ValueError:
        return False

    return True


def release(user_id, team_id, branch_name, row_id):
    pyBot.send_message(team_id, user_id, "You are at the front of the queue. I'll now merge master into your branch")
    merge_response = github.merge_master_into_branch(branch_name)
    if 'message' in merge_response and merge_response['message'] == 'Merge Conflict':
        pyBot.remove_from_queue(row_id)
        pyBot.send_message(team_id, user_id,
                           "I've not been able to merge master into {} because of merge conflicts. :cry: I've removed "
                           "you from the queue. Once the conflicts are fixed, re-join the queue".format(branch_name))
    else:
        pyBot.send_message(team_id, user_id, "I've merged master into your branch :merge: "
                                             "I'll run the Jenkins validation now")
        github.trigger_jenkins_test_run(row_id, branch_name)


@app.route("/install", methods=["GET"])
def pre_install():
    client_id = pyBot.oauth["client_id"]
    scope = pyBot.oauth["scope"]

    return render_template("install.html", client_id=client_id, scope=scope)


@app.route("/thanks", methods=["GET", "POST"])
def thanks():

    code_arg = request.args.get('code')

    pyBot.auth(code_arg)
    return render_template("thanks.html")


@app.route("/success", methods=["POST"])
def success():
    row_id = request.args['row_id']
    job_name = request.args['job']
    queue_entry = pyBot.get_queue_entry_by_row_id(row_id)
    team_id = queue_entry['team_id']
    user_id = queue_entry['user_id']
    if job_name == 'validation':
        pyBot.send_message(team_id, user_id,"The validation has passed :ok_hand: I'll merge your pull request now.'")
        # response = github.merge_pull_request(queue_entry['pull_request_id'])
        # print(response)
        # if response.status_code == 200:
        if True:
            message = "Pull request merged successfully. Which version do you want to release this under? You can put " \
                      "either a single number or v{number}"
        else:
            message = "Pull request failed: You have been removed from the queue. Please check your PR can be merged."
            pyBot.remove_from_queue(row_id)

        pyBot.send_message(team_id, user_id, message)
    else:
        pyBot.send_message(team_id, user_id, "I've released your branch. Congratulations :parrotultrafast:")
        pyBot.remove_from_queue(row_id)
        queue = pyBot.get_current_queue()
        if len(queue) > 0:
            top_entry = queue[0]
            release(top_entry['user_id'], top_entry['team_id'], top_entry['branch_name'], top_entry['row_id'])
    return make_response('Hello')


@app.route("/failure", methods=["POST"])
def failure():
    row_id = request.args['row_id']
    queue_entry = pyBot.get_queue_entry_by_row_id(row_id)
    pyBot.send_message(queue_entry['team_id'], queue_entry['user_id'], "The jenkins validation has failed. "
                                                                       "I've removed you from the queue. Once "
                                                                       "you've fixed the errors in the build, "
                                                                       "rejoin the queue")
    pyBot.remove_from_queue(row_id)
    return make_response('Hello')


@app.route("/listening", methods=["GET", "POST"])
def hears():
    slack_event = json.loads(request.data)
    # Return error if team ID and other bits are incorrect

    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"content_type":
                                                             "application/json"
                                                             })

    if "event" in slack_event:
        event_type = slack_event["event"]["type"]
        _event_handler(event_type, slack_event)
        return make_response('Hello')

    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})


if __name__ == '__main__':
    app.run(debug=True)
