import json
import sys
import logging
import plugin
import datetime
import re

class Bojo(plugin.Plugin):

    def __init__(self):
        plugin.Plugin.__init__(self, "bojo")
        self.settings = {}
        self.channels_watching = {}
        self.is_ready = {}
        self.topics = {}
        self.nick = ''
        self.update_times = {}
        self.servers = []

    def nick_extract(self, target):
        return target.split('!')[0].lower()

    def started(self, settings):
        self.settings = json.loads(settings)
        self.nick = self.settings.get('nickname')

    def update(self, *args):
        for server in self.servers:
            now = datetime.datetime.now()
            update_time = self.update_times.get(server)
            if update_time and now > update_time:
                self.update_times[server] = update_time + datetime.timedelta(hours=24)
                channels = self.settings.get(server).get('channelstowatch')
                for channel in channels:
                    self.join(server, channel)

    def on_welcome(self, server, source, target, message):
        logging.info("welcome" + server)
        self.servers.append(server)

    def on_umode(self, server, source, target, modes):
        logging.info('on_umode: ' + modes)
        if modes == '+r':
            self._registered(server)

    def _registered(self, server):
        channels = self.settings.get(server).get('channelstowatch')
        self.channels_watching[server] = channels
        for channel in channels:
            self._set_update_time(server, channel)

    def _set_update_time(self, server, channel):
        join_time_str = self.settings.get(server).get('jointime')
        join_time = datetime.datetime.strptime(join_time_str, '%H:%M').time()
        update_time = datetime.datetime.combine(datetime.date.today(), join_time)
        now = datetime.datetime.now()
        diff = update_time - now
        if diff.days < 0:
            update_time += datetime.timedelta(hours=24)
        self.update_times[server] = update_time

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
                    if target == self.nick.lower():
                        if mode == 'h' and adding:
                            logging.info('acquired +h')
                            server_channels_map = self.is_ready.get(server, {})
                            server_channels_map[channel] = True
                            self.is_ready[server] = server_channels_map
                            self.topic(server, channel)

    def on_currenttopic(self, server, source, target, channel, topic):
        if channel in self.settings.get(server).get('channelstowatch') and self.is_ready.get(server, {}).get(channel):
            logging.info("currenttopic " + channel + " " + topic)
            suffix = self.settings.get(server).get("countdownsuffix")
            countdown_str = self.settings.get(server).get("countdowndate")
            countdown = datetime.datetime.strptime(countdown_str, "%Y-%m-%d %H:%M")
            now = datetime.datetime.now()
            days_left = (countdown - now).days
            if not suffix in topic:
                self.topic(server, channel, topic.strip() + " | " + str(days_left) + " " + suffix)
            else:
                p = re.compile('(.*)( \d+)( ' + suffix + '.*)')
                result = p.sub('\g<1> ' + str(days_left) + '\g<3>', topic)
                self.topic(server, channel, result)
            self.part(server, channel, self.settings.get(server).get('partmessage', ''))

    def on_privmsg(self, server, source, target, message):
        source_nick = self.nick_extract(source)
        logging.info("privmsg from " + source_nick + ": " + message)
        if message == 'ready':
            logging.info("ready")
            self.privmsg(server, source_nick, str(self.is_ready))

if __name__ == "__main__":
    sys.exit(Bojo.run())
