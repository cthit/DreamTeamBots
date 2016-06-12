import json
import sys
import logging
import plugin


class Anette(plugin.Plugin):

    def __init__(self):
        plugin.Plugin.__init__(self, "anette")
        self.settings = {}
        self.is_registering = False
        self.modes = []
        self.channel_modes = {}

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
        print(modes)
        if modes.startswith('+'):
            for m in modes[1:]:
                channel_modes.append(m)
        elif modes.startswith('-'):
            for m in modes[1:]:
                channel_modes.remove(m)

        self.channel_modes[server][channel] = channel_modes


    def on_mode(self, server, source, channel, modes, target):
        target = target.lower()
        print('botname', self.name, target)
        if target == self.name:
            self._add_channel_modes(server, channel, modes)

    def on_join(self, server, source, channel):
        source_nick = self._nick(source).lower()
        print('on_join', server, source, channel)
        if (not self.name == source_nick) and channel in self.channels_watching:
            self._new_join(server, source_nick, channel)

    def _new_join(self, server, source_nick, channel):
        print('new join', server, source_nick, channel)
        self._voice(server, source_nick, channel)

    def _voice(self, server, target_nick, channel):
        print("voicing")
        self.privmsg(server, target_nick, "Hello there")
        try:
            self.mode(server, channel, '+v ' + target_nick)
            logging.info("past self.mode()")
            print("past self.mode()")
        except Exception as e:
            logging.error(e)

    def _registered(self, server):
        self.is_registering = False
        channels = self.settings.get(server).get('channelstowatch')
        self.channels_watching = channels
        for chan in channels:
            self.join(server, chan)

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
        print("privnotice", message)
        print(source, target)
        if message == 'modes':
            print("modes")
            self.send_modes(server, source)

    def send_modes(self, server, target):
        self.privmsg(server, self._nick(target), str(self.modes))
        self.privmsg(server, self._nick(target), str(self.channel_modes))


if __name__ == "__main__":
    try:
        sys.exit(Anette.run())
    except Exception as e:
        logging.error('Fucked up: %r' % e)
