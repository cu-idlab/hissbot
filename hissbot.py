import os
import logging
import random
import json
from collections import Counter
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

with open('/var/www/this.json', 'w+') as f:
    try:
        this_counts = Counter(json.load(f))
    except:
        this_counts = Counter()

with open('/var/www/tension.json', 'w+') as f:
    try:
        tension_counts = Counter(json.load(f))
    except:
        tension_counts = Counter()

@slack_events_adapter.on("message")
def handle_channel_message(payload):
    print('Received message event.')
    event = payload.get("event", {})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')
    ts = event.get('ts')
    channel_type = event.get('channel_type')
    print('Received text: "{}" at {} from user {}. Channel type: {}'.format(text, ts, user_id, channel_type))

    if channel_type in ['group', 'channel'] and text:
        if 'this' in text.lower():
            this_counts[user_id] = this_counts.get(user_id, 0) + 1
            
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
            with open('/var/www/this.json', 'w') as f:
                json.dump(this_counts, f)

        if 'tension' in text.lower():
            tension_counts[user_id] = tension_counts.get(user_id, 0) + 1
            hiss_react = client.reactions_add(
                channel=channel_id,
                name='jedly',
                timestamp=ts
            )
            with open('/var/www/tension.json', 'w') as f:
                json.dump(tension_counts, f)

@slack_events_adapter.on("app_mention")
def handle_mention(payload):
    print('Received app_mention event.')
    event = payload.get("event", {})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')
    ts = event.get('ts')
    print('Received text: {} at {} from user {}'.format(text, ts, user_id))

    if text:
        text.replace('\xc2\xa0', ' ')
        tokens = text.split(' ')
        if len(tokens) == 2:
            if tokens[1] == 'stats':
                if len(this_counts) != 0 or len(tension_counts) != 0:
                    response = ''
                    for user_id in allowed_users:
                        user_info = client.users_info(user=user_id)
                        user_name = user_info['user']['profile']['display_name']
                        response += '*{}* \n _this_: {} times, _tension_: {} times. \n'.format(user_name, this_counts.get(user_id), tension_counts.get(user_id))

                    client.chat_postMessage(channel=channel_id, text=response)
                else: 
                    client.chat_postMessage(channel=channel_id, text='Nobody has said the magic words.')
            else:
                client.chat_postMessage(channel=channel_id, text='Hissbot can\'t do this yet.')
        else:
            client.chat_postMessage(channel=channel_id, text='Hissbot can\'t do this yet.')


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    app.run(port=3000)