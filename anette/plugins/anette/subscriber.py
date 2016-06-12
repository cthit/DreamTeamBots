import logging
from datetime import datetime

OFF = 0
ON = 1
ALL = 2

PUSH = 'push'
QUERY = 'query'


class Subscriber(object):

    def __init__(self, nick, modes):
        self.nick = nick
        self.status = ON
        self.modes = modes

    def to_dict(self):
        return {key:value for key, value in self.__dict__.items() if not key.startswith('__') and not callable(key)}

    @classmethod
    def from_dict(cls, dict):
        subscriber = Subscriber(
            dict.get('nick'),
            dict.get('modes')
        )
        subscriber.status = dict.get('status')

        return subscriber

    def renick(self, new_nick):
        self.nick = new_nick

    def update_status(self, status):
        if status in [OFF, ON, ALL]:
            self.status = status
        else:
            logging.warning("Invalid status %r" % status)

    def add_subscription_mode(self, mode):
        if mode in [PUSH, QUERY]:
            if mode not in self.modes:
                self.modes.append(mode)
        else:
            logging.warning("Invalid mode %r" % mode)

    def remove_subscription_mode(self, mode):
        try:
            self.modes.remove(mode)
        except ValueError as e:
            pass



