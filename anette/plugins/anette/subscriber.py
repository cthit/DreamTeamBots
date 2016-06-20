import logging
from datetime import datetime


class Subscriber(object):

    OFF = 0
    ON = 1
    ALL = 2

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
        if string == 'off':
            return Subscriber.OFF
        elif string == 'on':
            return  Subscriber.ON
        elif string == 'all':
            return Subscriber.ALL
        else:
            raise ValueError('No such status %r' % string)

    @staticmethod
    def status_from_int(i):
        if i == Subscriber.OFF:
            return 'off'
        elif i == Subscriber.ON:
            return 'on'
        elif i == Subscriber.ALL:
            return 'all'
        else:
            raise ValueError('No such status')

    @staticmethod
    def available_statuses():
        return ['off', 'on', 'all']

    @staticmethod
    def available_modes():
        return [Subscriber.QUERY]

    def renick(self, new_nick):
        self.nick = new_nick

    def update_status(self, status_string):
        logging.info("status_string: %r" % status_string)
        status = Subscriber.status_from_string(status_string)
        if status in [Subscriber.OFF, Subscriber.ON, Subscriber.ALL]:
            self.status = status
        else:
            logging.warning("Invalid status %r" % status)

    def add_subscription_mode(self, mode):
        if mode in Subscriber.available_modes():
            if mode not in self.modes:
                self.modes.append(mode)
        else:
            logging.warning("Invalid mode %r" % mode)

    def remove_subscription_mode(self, mode):
        try:
            self.modes.remove(mode)
        except ValueError as e:
            pass
