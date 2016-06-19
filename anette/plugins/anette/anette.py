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
        self.db_wrapper = {}
        self.nick = 'Anette'
        self.channels_pending_user_for_voicing = []

    def _nick(self, target):
        return target.split('!')[0]

    def started(self, settings):
        self.settings = json.loads(settings)

    def on_welcome(self, server, source, target, message):
        pass

    def _person_devoiced(self, server, nick):
        logging.info('person devoiced: ' + nick)
        wrapper = self.db_wrapper.get(server)
        wrapper.set_nollan_fake(nick)
        wrapper.add_gamle(nick)

    def _person_voiced(self, server, nick):
        wrapper = self.db_wrapper.get(server)
        wrapper.add_nollan(Nollan(nick=nick))
        wrapper.remove_gamle_with_nick(nick)

    def on_join(self, server, source, channel):
        if not self.is_ready:
            return

        source_nick = self._nick(source)
        if (not self.nick == source_nick) and channel in self.channels_watching:
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

    def _voice(self, server, target, channel):
        self.mode(server, channel, '+v ' + target)

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
        logging.info('on_umode: ' + modes)
        if modes == '+r':
            self._registered(server)

    def on_mode(self, server, source, channel, modes, target):
        target_nick = self._nick(target)
        if target_nick == self.nick:
            if modes == '+h':
                self._voice_previously_unvoiced_nollan(server, channel)
        else:
            if modes == '-v':
                self._person_devoiced(server, target_nick)
            elif modes == '+v':
                self._person_voiced(server, target_nick)

    def _voice_previously_unvoiced_nollan(self, server, channel):
        logging.info('_voice_previously_unvoiced_nollan ' + channel)
        self.channels_pending_user_for_voicing.append(channel)
        self.names(server, channel)

    def on_namreply(self, server, source, target, op, channel, names_with_modes):
        logging.info("on_names:" + channel)
        if not self.is_ready:
            return

        names = [self._strip_nick_of_mode(n.strip())
                 for n in names_with_modes.split(" ")
                 if len(n.strip()) > 0]
        logging.info(names)

        try:
            self.channels_pending_user_for_voicing.remove(channel)
        except ValueError as e:
            pass

        for nick in names:
            if nick != self.nick and self._is_nollan(server, nick):
                self._voice(server, nick, channel)

    def _strip_nick_of_mode(self, nick):
        for m in ['+', '%', '@', '&', '~']:
            if nick.startswith(m):
                return nick[1:]

        return nick

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
