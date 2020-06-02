#!/root/anaconda3/bin/python

import os
import logging
import random
import json
from flask import Flask
from slack import WebClient
from slackeventsapi import SlackEventAdapter

allowed_users = ['U16JR6M26' #jed
                ] 

with open('/var/www/hissbot-config.json') as f:
    config = json.load(f)

app = Flask(__name__)
slack_events_adapter = SlackEventAdapter(config['HISSBOT_SIGNING_SECRET'], '/', app)

client = WebClient(token=config['HISSBOT_OAUTH_TOKEN'])

@slack_events_adapter.on("message")
def hiss(payload):
    event = payload.get("event", {})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')
    ts = event.get('ts')
    print('Received text: {} at {} from user {}'.format(text, ts, user_id))

    if text and ('this' in text.lower()):
        hiss_react = client.reactions_add(
            channel=channel_id,
            name='hiss',
            timestamp=ts
        )

        if random.randint(1,100) <= 50:
            hiss_react = client.reactions_add(
                channel=channel_id,
                name='jed',
                timestamp=ts
            )
        else:
            hiss_react = client.reactions_add(
                channel=channel_id,
                name='jedly',
                timestamp=ts
            )

if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    app.run(port=3000)