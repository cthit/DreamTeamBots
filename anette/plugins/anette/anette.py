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
from pushbullet_service import PushbulletService

class Anette(plugin.Plugin):

    def __init__(self):
        plugin.Plugin.__init__(self, "anette")
        self.settings = {}
        self.is_ready = False
        self.db_wrapper = {}
        self.controllers = {}
        self.channels_watching = {}
        self.pushbullets = {}
        self.channels_pending_user_for_voicing = []

    def nick_extract(self, target):
        return target.split('!')[0].lower()

    def started(self, settings):
        self.settings = json.loads(settings)
        self.nick = self.settings.get('nickname')

    def on_welcome(self, server, source, target, message):
        pass

    def on_join(self, server, source, channel):
        if not self.is_ready:
            return

        source_nick = self.nick_extract(source)
        logging.info(source_nick + ' joined ' + channel)
        if (not self.nick == source_nick) and channel in self.channels_watching.get(server, []):
            self.controllers[server].new_join(server, source_nick, channel)

    def voice(self, server, target, channel):
        logging.info('voicing ' + target + ' in ' + channel)
        self.mode(server, channel, '+v ' + target)

    def devoice(self, server, target, channel):
        logging.info('devoicing ' + target + ' in ' + channel)
        self.mode(server, channel, '-v ' + target)

    def _registered(self, server):
        channels = self.settings.get(server).get('channelstowatch')
        self.channels_watching[server] = channels
        self._setup_db(server)
        self._load_gamble(server)
        self._setup_pushbullet(server)
        for chan in channels:
            self.join(server, chan)

        logging.info("Registered and ready")
        self.is_ready = True

    def _load_gamble(self, server):
        logging.info('loading gamble')
        try:
            fname = self.settings.get(server).get('gamblefile')
            if os.path.isfile(fname):
                logging.info('opening gamble file')
                file = open(fname, 'r')
                wrapper = self.db_wrapper.get(server)
                for l in file:
                    gamble = l.strip()
                    if gamble:
                        wrapper.add_gamble(gamble)
                        logging.info('added ' + gamble + ' to gamble')
        except Exception as e:
            logging.error("Failed to load gamble file: " + self.settings.get(server).get('gamblefile'))

    def _setup_db(self, server):
        logging.info("Setup DB for: " + server)
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

    def _setup_pushbullet(self, server):
        pushbullet_settings = self.settings.get(server).get("pushbullet")
        self.pushbullets[server] = PushbulletService(access_token=pushbullet_settings.get("access_token"),
                                                     tags=pushbullet_settings.get("tags"))

    def on_umode(self, server, source, target, modes):
        logging.info('on_umode: ' + modes)
        if modes == '+r':
            self._registered(server)

    def on_mode(self, server, source, channel, modes, *targets):
        logging.info('mode change ' + modes + ' ' + str(targets))
        user_modes = ['q', 'a', 'o', 'h', 'v', 'b']
        ti = 0
        adding = True
        for i in range(0, len(modes)):
            mode = modes[i]
            if mode == '+':
                adding = True
            elif mode == '-':
                adding = False
            else:
                if mode in user_modes:
                    target = targets[ti].lower()
                    ti += 1
                    self._handle_mode_change(adding, channel, mode, server, target)

    def _handle_mode_change(self, adding, channel, mode, server, target):
        if target == self.nick.lower():
            if mode == 'h' and adding:
                logging.info('acquired +h')
                self.controllers[server].voice_previously_unvoiced_nollan(server, channel)
        else:
            if mode == 'v' and not adding:
                self.controllers[server].person_devoiced(server, target)
            elif mode == 'v' and adding:
                self.controllers[server].person_voiced(server, target)

    def on_namreply(self, server, source, target, op, channel, names_with_modes):
        logging.info("on_names:" + channel)
        if not self.is_ready:
            return

        names = [self._strip_nick_of_mode(n.strip()).lower()
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

    def _is_admin(self, server, source):
        nick = self.nick_extract(source)
        return nick.lower() in self.settings.get(server).get('admins')

    def _is_gamble(self, server, source):
        nick = self.nick_extract(source)
        return self.controllers[server].is_gamble(nick.lower())

    def on_privmsg(self, server, source, target, message):
        source_nick = self.nick_extract(source)
        logging.info('received msg from ' + source_nick + ': ' + message)
        if self._is_gamble(server, source):
            logging.info(source_nick + ' is gamble')
            message = message.lower()
            if message.startswith('subscribe status'):
                self.controllers[server]\
                    .subscribe_status(server, source, target, self._strip_msg_of_prefix(message, 'subscribe status'))
            elif message.startswith('subscribe'):
                self.privmsg(server, self.nick_extract(source), 'did you mean "subscribe status"?')
            elif message.startswith('help'):
                self.controllers[server]\
                    .send_help(server, source, target, self._is_admin(server, source),
                               self._strip_msg_of_prefix(message, 'help'))
            elif message.startswith('voice') and self._is_admin(server, source):
                self.controllers[server]\
                    .voice_nollan(self._strip_msg_of_prefix(message, 'voice'))
            elif message.startswith('devoice') and self._is_admin(server, source):
                self.controllers[server]\
                    .devoice_gamble(self._strip_msg_of_prefix(message, 'devoice'))
            elif message.startswith('join') and self._is_admin(server, source):
                self.controllers[server]\
                    .join_channel(server, source, self._strip_msg_of_prefix(message, 'join'))

if __name__ == "__main__":
    sys.exit(Anette.run())
