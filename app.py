# -*- coding: utf-8 -*-

import json
import bot
from flask import Flask, request, make_response, render_template

pyBot = bot.Bot()
slack = pyBot.client

app = Flask(__name__)


def _event_handler(event_type, slack_event):
    if event_type == "message" and "event" in slack_event and "user" in slack_event["event"]:
        print(slack_event)
        team_id = slack_event['team_id']
        user_id = slack_event['event']['user']
        print(team_id)
        print(slack_event)
        print(event_type)
        pyBot.onboarding_message(team_id, user_id)
        return make_response(event_type, 200, {"X-Slack-No-Retry": 1})


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


@app.route("/listening", methods=["GET", "POST"])
def hears():
    slack_event = json.loads(request.data)

    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"content_type":
                                                             "application/json"
                                                             })

    if "event" in slack_event:
        event_type = slack_event["event"]["type"]
        return _event_handler(event_type, slack_event)

    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})


if __name__ == '__main__':
    app.run(debug=True)
