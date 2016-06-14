
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
        if not self.gamle_table.get(Query().nick == nick):
            self.gamle_table.insert({'nick': nick})
            self.gamle_table.all()

    def find_gamle_with_nick(self, nick):
        GamleQuery = Query()
        return self.gamle_table.get(GamleQuery.nick == nick)

    def find_nollan_with_nick(self, nick):
        NollanQuery = Query()
        res = self.nollan_table.get(NollanQuery.nick == nick)
        return Nollan.from_dict(res) if res else None

    def set_nollan_fake(self, nick):
        nollan = self.find_nollan_with_nick(nick)
        if nollan:
            nollan.set_fake()
            self.nollan_table.update(nollan.to_dict(), eids=[nollan.eid])
            self.nollan_table.all()

    def find_subscribers_with_status(self, status):
        SubscriberQuery = Query()
        res = self.subscriber_table.search(SubscriberQuery.status == status)

        return (Subscriber.from_dict(s) for s in res)

    def _find_subscriber_with_nick(self, nick):
        SubscriberQuery = Query()
        res = self.subscriber_table.get(SubscriberQuery.nick == nick)
        return Subscriber.from_dict(res) if res else None

    def subscribe_status(self, nick, status):
        subscriber = self._find_subscriber_with_nick(nick)
        if subscriber:
            subscriber.update_status(status)
        else:
            subscriber = Subscriber(nick, Subscriber.status_from_string(status))

        if hasattr(subscriber, 'eid'):
            self.subscriber_table.update(subscriber.to_dict(), eids=[subscriber.eid])
        else:
            self.subscriber_table.insert(subscriber.to_dict())
        self.subscriber_table.all()

        return subscriber

    def subscribe_mode(self, nick, op, mode):
        subscriber = self._find_subscriber_with_nick(nick)
        if not subscriber:
            subscriber = Subscriber(nick, Subscriber.status_from_string('on'))

        if op == 'add':
            subscriber.add_subscription_mode(mode)
        elif op == 'remove':
            subscriber.remove_subscription_mode(mode)

        if hasattr(subscriber, 'eid'):
            self.subscriber_table.update(subscriber.to_dict(), eids=[subscriber.eid])
        else:
            self.subscriber_table.insert(subscriber.to_dict())
        self.subscriber_table.all()

        return subscriber
