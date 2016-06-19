import json
import sys
import logging
import plugin
import os.path
from tinydb import TinyDB
from dbwrapper import DBWrapper
from nollan import Nollan
from subscriber import Subscriber
from anette_controller import AnetteController


class Anette(plugin.Plugin):

    def __init__(self):
        plugin.Plugin.__init__(self, "anette")
        self.settings = {}
        self.is_ready = False
        self.db_wrapper = {}
        self.controllers = {}
        self.channels_watching = {}
        self.channels_pending_user_for_voicing = []

    def nick_extract(self, target):
        return target.split('!')[0]

    def started(self, settings):
        self.settings = json.loads(settings)
        self.nick = self.settings.get('nickname')

    def on_welcome(self, server, source, target, message):
        pass

    def on_join(self, server, source, channel):
        if not self.is_ready:
            return

        source_nick = self.nick_extract(source)
        if (not self.nick == source_nick) and channel in self.channels_watching.get(server, []):
            self.controllers[server].new_join(server, source_nick, channel)

    def voice(self, server, target, channel):
        self.mode(server, channel, '+v ' + target)

    def _registered(self, server):
        channels = self.settings.get(server).get('channelstowatch')
        self.channels_watching[server] = channels
        self._setup_db(server)
        self._load_gamble(server)
        for chan in channels:
            self.join(server, chan)

        logging.info("Registered and ready")
        self.is_ready = True

    def _load_gamble(self, server):
        try:
            fname = self.settings.get(server).get('gamblefile')
            if os.path.isfile(fname):
                file = open(fname, 'r')
                wrapper = self.db_wrapper.get(server)
                for l in file:
                    wrapper.add_gamble(l.strip())
        except Exception as e:
            logging.error("Failed to load gamblefile: " + self.settings.get(server).get('gamblefile'))

    def _setup_db(self, server):
        logging.info("Setup DB for: " + server)
        logging.info(self.db)
        if not self.is_ready:
            db_path = self.settings.get('db_path', '') + 'anette_db.json'
            logging.info("DB path:" + db_path)
            self.db = TinyDB(db_path)
            logging.info('DB initiated')

        if not self.db_wrapper.get(server):
            wrapper = DBWrapper(server, self.db)
            self.db_wrapper[server] = wrapper
            self.controllers[server] = AnetteController(plugin=self, wrapper=wrapper, server=server)
            logging.info('DB wrapper initiated')

    def on_umode(self, server, source, target, modes):
        logging.info('on_umode: ' + modes)
        if modes == '+r':
            self._registered(server)

    def on_mode(self, server, source, channel, modes, target):
        target_nick = self.nick_extract(target)
        if target_nick == self.nick:
            if modes == '+h':
                self.controllers[server].voice_previously_unvoiced_nollan(server, channel)
        else:
            if modes == '-v':
                self.controllers[server].person_devoiced(server, target_nick)
            elif modes == '+v':
                self.controllers[server].person_voiced(server, target_nick)

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

        self.controllers[server].nicks_received(server, channel, names)

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
            self.controllers[server].subscribe_status(server, source, target, self._strip_msg_of_prefix(message, 'subscribe status'))
        elif message.startswith('subscribe mode'):
            self.controllers[server].subscribe_mode(server, source, target, self._strip_msg_of_prefix(message, 'subscribe mode'))
        elif message.startswith('help'):
            self.controllers[server].send_help(server, source, target, self._strip_msg_of_prefix(message, 'help'))

if __name__ == "__main__":
    sys.exit(Anette.run())
