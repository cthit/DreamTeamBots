
from datetime import datetime


class Nollan(object):

    def __init__(self, nick):
        self.nick = nick
        self.old_nicks = []
        self.last_seen = datetime.now().isoformat()  # Fix timezone?
        self.first_seen = datetime.now().isoformat()
        self.fake = False

    def to_dict(self):
        return {key:value for key, value in self.__dict__.items() if not key.startswith('__') and not callable(key)}

    @classmethod
    def from_dict(cls, dict):
        nollan = Nollan(dict.get('nick'))
        nollan.old_nicks = dict.get('old_nicks')
        nollan.last_seen = dict.get('last_seen')
        nollan.first_seen = dict.get('first_seen')
        nollan.fake = dict.get('fake')
        nollan.eid = dict.eid

        return nollan

    def add_nick_to_old_nicks(self, nick):
        self.old_nicks.append(nick)

    def renick(self, new_nick):
        self.old_nicks.append(self.nick)
        self.nick = new_nick

    def update_last_seen(self):
        self.last_seen = datetime.now()

    def set_fake(self):
        self.fake = True

    def set_unfake(self):
        self.fake = False
