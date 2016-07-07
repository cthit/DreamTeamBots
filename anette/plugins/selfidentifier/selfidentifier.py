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
        self.nick = ''

    def nick_extract(self, target):
        return target.split('!')[0]

    def started(self, settings):
        self.settings = json.loads(settings)
        self.nick = self.settings.get('nickname')

    def on_welcome(self, server, source, target, message):
        self.channel_modes[server] = {}
        if server in self.settings:
            auth = self.settings.get(server).get("auth")
            self.is_registering = True
            self.privmsg(server, auth.get("target"), 'identify ' + auth.get('pass'))

    def _add_channel_modes(self, server, channel, modes):
        logging.info('adding channel modes ' + modes)
        channel_modes = self.channel_modes.get(server).get(channel, [])
        if modes.startswith('+'):
            for m in modes[1:]:
                channel_modes.append(m)
        elif modes.startswith('-'):
            for m in modes[1:]:
                channel_modes.remove(m)

        self.channel_modes[server][channel] = channel_modes

    def on_mode(self, server, source, channel, modes, *targets):
        logging.info('mode change ' + modes + ' ' + str(targets))
        user_modes = ['q', 'a', 'o', 'h', 'v', 'b']
        func = self._add_mode
        ti = 0
        for i in range(0, len(modes)):
            mode = modes[i]
            if mode == '+':
                func = self._add_mode
            elif mode == '-':
                func = self._remove_mode
            else:
                if mode in user_modes:
                    target = targets[ti]
                    ti += 1
                    if target.lower() == self.nick.lower():
                        func(server, channel, mode)

    def _add_mode(self, server, channel, mode):
        channel_modes = self.channel_modes.get(server).get(channel, [])
        channel_modes.append(mode)
        self.channel_modes[server][channel] = channel_modes

    def _remove_mode(self, server, channel, mode):
        channel_modes = self.channel_modes.get(server).get(channel, [])
        try:
            channel_modes.remove(mode)
        except ValueError:
            pass
        self.channel_modes[server][channel] = channel_modes

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
        self.privmsg(server, self.nick_extract(target), str(self.channel_modes.get(server, {})))


if __name__ == "__main__":
    sys.exit(SelfIdentifier.run())
