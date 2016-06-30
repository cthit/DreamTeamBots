import json
import sys
import logging
import plugin


class Bojo(plugin.Plugin):

    def __init__(self):
        plugin.Plugin.__init__(self, "bojo")
        self.settings = {}
        self.channels_watching = {}
        self.is_ready = {}
        self.topics = {}

    def nick_extract(self, target):
        return target.split('!')[0]

    def started(self, settings):
        self.settings = json.loads(settings)

    def on_welcome(self, server, source, target, message):
        logging.info("welcome" + server)

    def on_umode(self, server, source, target, modes):
        logging.info('on_umode: ' + modes)
        if modes == '+r':
            self._registered(server)

    def _registered(self, server):
        channels = self.settings.get(server).get('channelstowatch')
        self.channels_watching[server] = channels

    def on_mode(self, server, source, channel, modes, target):
        target = target.lower()
        if target == self.settings.get('nick'):
            if modes.startswith('+') and 'h' in modes:
                server_channels_map = self.is_ready.get(server, {})
                server_channels_map[channel] = True
                self.is_ready[server] = server_channels_map

    def perform(self, server, channel):
        self.topic(server, channel)

    def on_currenttopic(self, server, source, target, channel, topic):
        if channel in self.settings.get(server).get('channelstowatch') and self.is_ready.get(server, {}).get(channel):
            logging.info("currenttopic " + channel + " " + topic)

    def on_privmsg(self, server, source, target, message):
        logging.info("privmessagederp")
        logging.info(message)
        if message == 'ready':
            logging.info("ready")
            logging.info("nick" + self.nick_extract(source))
            self.privmsg(server, self.nick_extract(source), "READY")
            self.privmsg(server, self.nick_extract(source), str(self.is_ready))





if __name__ == "__main__":
    sys.exit(Bojo.run())
