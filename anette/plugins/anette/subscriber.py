import logging
from datetime import datetime


class Subscriber(object):

    OFF = 0
    ON = 1
    ALL = 2

    STATUSES = {
        "off": OFF,
        "on": ON,
        "all": ALL

    }

    PUSH = 'push'
    QUERY = 'query'

    def __init__(self, nick, status):
        self.nick = nick
        self.status = status
        self.modes = [Subscriber.QUERY]

    def to_dict(self):
        return {key:value for key, value in self.__dict__.items() if not key.startswith('__') and not callable(key)}

    @classmethod
    def from_dict(cls, dict):
        subscriber = Subscriber(
            dict.get('nick'),
            dict.get('modes')
        )
        subscriber.status = dict.get('status')
        subscriber.eid = dict.eid

        return subscriber

    @staticmethod
    def status_from_string(string):
        status = Subscriber.STATUSES.get(string)
        if status:
            return status
        else:
            raise ValueError('No such status')

    @staticmethod
    def available_statuses():
        return Subscriber.STATUSES.keys()

    @staticmethod
    def available_modes():
        return [Subscriber.QUERY, Subscriber.PUSH]

    def renick(self, new_nick):
        self.nick = new_nick

    def update_status(self, status):
        if status in [Subscriber.OFF, Subscriber.ON, Subscriber.ALL]:
            self.status = status
        else:
            logging.warning("Invalid status %r" % status)

    def add_subscription_mode(self, mode):
        if mode in [Subscriber.PUSH, Subscriber.QUERY]:
            if mode not in self.modes:
                self.modes.append(mode)
        else:
            logging.warning("Invalid mode %r" % mode)

    def remove_subscription_mode(self, mode):
        try:
            self.modes.remove(mode)
        except ValueError as e:
            pass



