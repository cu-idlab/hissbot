import os
import logging
import random
import json
import re
from collections import Counter
from flask import Flask, jsonify, request
from slack import WebClient
from slackeventsapi import SlackEventAdapter

BOT_USERID = 'U014YHFD3KK'

allowed_users = ['U16JR6M26' #jed
                ] 

with open('/var/www/hissbot-config.json') as f:
    config = json.load(f)

app = Flask(__name__)
slack_events_adapter = SlackEventAdapter(config['HISSBOT_SIGNING_SECRET'], '/', app)

client = WebClient(token=config['HISSBOT_OAUTH_TOKEN'])

try:
    with open('/var/www/this.json', 'r') as f:    
        this_counts = Counter(json.load(f))
except:
    this_counts = Counter()

try: 
    with open('/var/www/tension.json', 'r') as f:
        tension_counts = Counter(json.load(f))
except:
    tension_counts = Counter()

try:
    with open('/var/www/altchi.json', 'r') as f:
        altchi_counts = Counter(json.load(f))
except:
    altchi_counts = Counter()

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

    if channel_type in ['group', 'channel'] and text and user_id:
        text = re.sub('\s+', ' ', text)
        if re.search(r'\bt+h+i+s+\b', text, re.IGNORECASE): # 'this' in text.lower():
            print('User id count before: {}'.format(this_counts.get(user_id)))
            this_counts[user_id] = this_counts.get(user_id, 0) + 1
            print('User id count after: {}'.format(this_counts.get(user_id)))
            
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

        if re.search(r'\btension\b', text, re.IGNORECASE):
            tension_counts[user_id] = tension_counts.get(user_id, 0) + 1
            hiss_react = client.reactions_add(
                channel=channel_id,
                name='jedly',
                timestamp=ts
            )
            with open('/var/www/tension.json', 'w') as f:
                json.dump(tension_counts, f)

        if re.search(r'\balt\.chi\b', text, re.IGNORECASE):
            altchi_counts[user_id] = altchi_counts.get(user_id, 0) + 1
            hiss_react = client.reactions_add(
                channel=channel_id,
                name='cartoonjed',
                timestamp=ts
            )
            with open('/var/www/altchi.json', 'w') as f:
                json.dump(altchi_counts, f)

# @slack_events_adapter.on("app_mention")
# def handle_mention(payload):
#     print('Received app_mention event.')
#     event = payload.get("event", {})
#     channel_id = event.get('channel')
#     user_id = event.get('user')
#     text = event.get('text')
#     ts = event.get('ts')
#     print('Received text: {} at {} from user {}'.format(text, ts, user_id))

#     if text:
#         text = re.sub('\s+', ' ', text)
#         print('Cleaned text: {}'.format(text))
#         tokens = text.split(' ')
#         print(tokens)
#         if len(tokens) == 2:
            
#             if tokens[1] == 'stats':
#                 if len(this_counts) != 0 or len(tension_counts) != 0:
#                     response = ''
#                     for user_id in set(this_counts.keys()).union(set(tension_counts.keys())):
#                         user_info = client.users_info(user=user_id)
#                         user_name = user_info['user']['profile']['display_name']
#                         response += '*{}* \n _this_: {} times, _tension_: {} times. \n'.format(user_name, this_counts.get(user_id, 0), tension_counts.get(user_id, 0))

#                     client.chat_postMessage(channel=channel_id, text=response)
#                 else: 
#                     client.chat_postMessage(channel=channel_id, text='Nobody has said the magic words.')
#             else:
#                 client.chat_postMessage(channel=channel_id, text='Hissbot can\'t do this yet.')
#         else:
#             client.chat_postMessage(channel=channel_id, text='Hissbot can\'t do this yet.')

@app.route('/stats', methods=['POST'])
def stats():

    if len(this_counts) != 0 or len(tension_counts) != 0 or len(altchi_counts) != 0:
        response = ''
        for user_id in set(this_counts.keys()).union(set(tension_counts.keys())).union(set(altchi_counts.keys())):
            try:
                user_info = client.users_info(user=user_id)
                user_name = user_info['user']['profile']['display_name']
            except:
                user_name = 'UNKNOWN'
            response += '*{}* \n _this_: {} times, _tension_: {} times, _alt.chi_: {} times. \n'.format(user_name, this_counts.get(user_id, 0), tension_counts.get(user_id, 0), altchi_counts.get(user_id, 0))
    else:
        response = 'Nobody has said the magic words.'
    payload = {'response_type': 'in_channel',
                'text': response}

    return jsonify(payload)


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    app.run(port=3000)