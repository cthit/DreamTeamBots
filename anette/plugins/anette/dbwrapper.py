
from tinydb import Query
from nollan import Nollan
from subscriber import Subscriber


class DBWrapper(object):

    def __init__(self, prefix, db):
        self.db = db
        self.nollan_table = self.db.table(prefix+':nollan')
        self.gamle_table = self.db.table(prefix+':gamle')
        self.subscriber_table = self.db.table(prefix+':subscriber')

    def add_nollan(self, nollan):
        self.nollan_table.insert(nollan.to_dict())
        self.nollan_table.all()

    def add_gamle(self, nick):
        self.gamle_table.insert({'nick': nick})
        self.gamle_table.all()

    def find_gamle_with_nick(self, nick):
        GamleQuery = Query()
        res = self.gamle_table.search(GamleQuery.nick == nick)
        if res:
            return res[0]

    def find_nollan_with_nick(self, nick):
        NollanQuery = Query()
        res = self.nollan_table.search(NollanQuery.nick == nick)
        if res:
            return res[0]

    def set_nollan_fake(self, nick):
        nollan_resp = self.find_nollan_with_nick(nick)
        if nollan_resp:
            nollan = Nollan.from_dict(nollan_resp)
            nollan.set_fake()
            self.nollan_table.insert(nollan.to_dict())
            self.nollan_table.all()
