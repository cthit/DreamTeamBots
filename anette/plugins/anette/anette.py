import json
import sys
import logging
import plugin
from tinydb import TinyDB
from dbwrapper import DBWrapper
from nollan import Nollan


class Anette(plugin.Plugin):

    def __init__(self):
        plugin.Plugin.__init__(self, "anette")
        self.settings = {}
        self.is_registering = False
        self.is_ready = False
        self.modes = []
        self.channel_modes = {}
        self.db_wrapper = {}

    def _nick(self, target):
        return target.split('!')[0]

    def started(self, settings):
        self.settings = json.loads(settings)

    def on_welcome(self, server, source, target, message):
        self.channel_modes[server] = {}
        if server in self.settings:
            auth = self.settings.get(server).get("auth")
            self.is_registering = True
            self.privmsg(server, auth.get("target"), 'identify ' + auth.get('pass'))

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
            self._check_if_new_and_if_so_add(server, source_nick)

    def _check_if_new_and_if_so_add(self, server, nick):
        wrapper = self.db_wrapper.get(server)
        if not wrapper.find_nollan_with_nick(nick):
            wrapper.add_nollan(Nollan(nick=nick))

    def _voice(self, server, target_nick, channel):
        self.mode(server, channel, '+v ' + target_nick)

    def _registered(self, server):
        self.is_registering = False
        channels = self.settings.get(server).get('channelstowatch')
        self.channels_watching = channels
        self._setup_db(server)
        for chan in channels:
            self.join(server, chan)

        logging.info("Registered and ready")
        self.is_ready = True

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

        if modes.startswith('+'):
            for m in modes[1:]:
                self.modes.append(m)
        elif modes.startswith('-'):
            for m in modes[1:]:
                self.modes.remove(m)

    def on_privmsg(self, server, source, target, message):
        if message == 'modes':
            self.send_modes(server, source)

    def send_modes(self, server, target):
        self.privmsg(server, self._nick(target), str(self.modes))
        self.privmsg(server, self._nick(target), str(self.channel_modes))


if __name__ == "__main__":
    sys.exit(Anette.run())
