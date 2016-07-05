
import requests
import json
import logging


class PushbulletService(object):

    def __init__(self, access_token, tags):
        self.access_token = access_token
        self.tags = tags

    def push_to_tag(self, tag, title, body):
        if tag not in self.tags:
            logging.warning("Unsupported tag: " + tag)
            return

        resp = requests.post('https://api.pushbullet.com/v2/pushes',
                             data=json.dumps({'body': body, 'title': title, 'type':'note', 'channel_tag': tag}),
                             headers={'Access-Token': self.access_token,'Content-Type': 'application/json'})
        if resp.status_code != 200:
            logging.warning("Push bullet tag push failed for tag %s with code %s" % (tag, str(resp.status_code)))

    def get_tags_available(self):
        return self.tags


