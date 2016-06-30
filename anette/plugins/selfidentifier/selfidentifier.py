import json
import sys
import logging

import plugin


class SelfIdentifier(plugin.Plugin):

    def __init__(self):
        plugin.Plugin.__init__(self, "selfidentifier")
        self.settings = {}
        self.is_registering = False
        self.modes = []
        self.channel_modes = {}

    def nick_extract(self, target):
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

    def _registered(self, server):
        self.is_registering = False

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
        self.privmsg(server, self.nick_extract(target), str(self.modes))
        self.privmsg(server, self.nick_extract(target), str(self.channel_modes))


if __name__ == "__main__":
    sys.exit(SelfIdentifier.run())
