import json
import sys
import logging
import plugin


class Bojo(plugin.Plugin):

    def __init__(self):
        plugin.Plugin.__init__(self, "bojo")
        self.settings = {}
        self.is_registering = False
        self.modes = []
        self.channel_modes = {}

    def _nick(self, target):
        return target.split('!')[0]

    def started(self, settings):
        self.settings = json.loads(settings)

    def on_welcome(self, server, source, target, message):
        pass

if __name__ == "__main__":
    sys.exit(Bojo.run())
