import json
import sys
import logging
import plugin
from tinydb import TinyDB
from dbwrapper import DBWrapper
from nollan import Nollan
from subscriber import Subscriber

class Anette(plugin.Plugin):

    def __init__(self):
        plugin.Plugin.__init__(self, "anette")
        self.settings = {}
        self.is_ready = False
        self.channel_modes = {}
        self.db_wrapper = {}

    def _nick(self, target):
        return target.split('!')[0]

    def started(self, settings):
        self.settings = json.loads(settings)

    def on_welcome(self, server, source, target, message):
        self.channel_modes[server] = {}

    def _add_channel_modes(self, server, channel, modes):
        channel_modes = self.channel_modes.get(server).get(channel, [])
        if modes.startswith('+'):
            for m in modes[1:]:
                channel_modes.append(m)
        elif modes.startswith('-'):
            for m in modes[1:]:
                channel_modes.remove(m)

        self.channel_modes[server][channel] = channel_modes

    def on_mode(self, server, source, channel, modes, target):
        target = target.lower()
        if target == self.name:
            self._add_channel_modes(server, channel, modes)
        elif '-v' in modes:
            self._person_devoiced(server, target)

    def _person_devoiced(self, server, nick):
        wrapper = self.db_wrapper.get(server)
        wrapper.set_nollan_fake(nick)
        wrapper.add_gamle(nick)

    def on_join(self, server, source, channel):
        if not self.is_ready:
            return

        source_nick = self._nick(source).lower()
        if (not self.name == source_nick) and channel in self.channels_watching:
            self._new_join(server, source_nick, channel)

    def _is_nollan(self, server, nick):
        wrapper = self.db_wrapper.get(server)
        if wrapper.find_gamle_with_nick(nick):
            return False
        else:
            return True

    def _new_join(self, server, source_nick, channel):
        if self._is_nollan(server, source_nick):
            self._voice(server, source_nick, channel)
            is_new = self._check_if_new_and_if_so_add(server, source_nick)
            self._notify_subscribers(server, source_nick, is_new)

    def _notify_subscribers(self, server, nick, is_new):
        subscriber_status = Subscriber.ON if is_new else Subscriber.ALL
        wrapper = self.db_wrapper.get(server)
        subscribers = wrapper.find_subscribers_with_status(subscriber_status)
        msg = nick + ' joined.'
        for subscriber in subscribers:
            self._notify(server, subscriber, msg)
            logging.info(msg + ' sent to ' + subscriber.nick)

    def _notify(self, server, subscriber, msg):
        if Subscriber.QUERY in subscriber.modes:
            self.privmsg(server, subscriber.nick, msg)

    def _check_if_new_and_if_so_add(self, server, nick):
        wrapper = self.db_wrapper.get(server)
        if not wrapper.find_nollan_with_nick(nick):
            wrapper.add_nollan(Nollan(nick=nick))
            return True
        else:
            return False

    def _voice(self, server, target_nick, channel):
        self.mode(server, channel, '+v ' + target_nick)

    def _registered(self, server):
        channels = self.settings.get(server).get('channelstowatch')
        self.channels_watching = channels
        self._setup_db(server)
        self._load_gamle(server)
        for chan in channels:
            self.join(server, chan)

        logging.info("Registered and ready")
        self.is_ready = True

    def _load_gamle(self, server):
        try:
            file = open(self.settings.get(server).get('gamlefile'), 'r')
            wrapper = self.db_wrapper.get(server)
            for l in file:
                wrapper.add_gamle(l.strip())
        except Exception as e:
            logging.error("Failed to load gamlefile: " + self.settings.get(server).get('gamlefile'))

    def _setup_db(self, server):
        logging.info("Setup DB for: " + server)
        logging.info(self.db)
        if not self.is_ready:
            db_path = self.settings.get('db_path', '') + 'anette_db.json'
            logging.info("DB path:" + db_path)
            self.db = TinyDB(db_path)
            logging.info('DB initiated')

        if not self.db_wrapper.get(server):
            self.db_wrapper[server] = DBWrapper(server, self.db)
            logging.info('DB wrapper initiated')

    def on_umode(self, server, source, target, modes):
        if modes == '+r':
            self._registered(server)

    def _strip_msg_of_prefix(self, msg, prefix):
        return msg[len(prefix):].strip()

    def on_privmsg(self, server, source, target, message):
        message = message.lower()
        if message.startswith('subscribe status'):
            self._subscribe_status(server, source, target, self._strip_msg_of_prefix(message, 'subscribe status'))
        elif message.startswith('subscribe mode'):
            self._subscribe_mode(server, source, target, self._strip_msg_of_prefix(message, 'subscribe mode'))

    def _subscribe_status(self, server, source, target, command):
        target_nick = self._nick(source)
        available = Subscriber.available_statuses()
        if command in available:
            wrapper = self.db_wrapper[server]
            wrapper.subscribe_status(target_nick, command)
            self.privmsg(server, target_nick, 'Subscription status set to ' + command)
        else:
            self.privmsg(server, target_nick,
                         'Invalid mode, only one the following are available: ' + ','.join(available))

    def _subscribe_mode(self, server, source, target, command):
        target_nick = self._nick(source)
        available = Subscriber.available_modes()
        parts = [p.strip() for p in command.split(' ')]
        error_msg = 'Invalid command: should be add/remove [mode] where mode is ' + ','.join(available)
        if len(parts) != 2:
            self.privmsg(server, target_nick, error_msg)
        else:
            [op, mode] = parts
            if mode in available and op in ['add', 'remove']:
                wrapper = self.db_wrapper[server]
                subscriber = wrapper.subscribe_mode(target_nick, op, mode)
                self.privmsg(server, target_nick, 'Updated modes, now: ' + str(subscriber.modes))
            else:
                self.privmsg(server, target_nick, error_msg)


if __name__ == "__main__":
    sys.exit(Anette.run())
