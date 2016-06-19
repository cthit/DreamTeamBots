import logging
from nollan import Nollan
from subscriber import Subscriber


class AnetteController(object):

    def __init__(self, plugin, wrapper):
        self.plugin = plugin
        self.wrapper = wrapper

    def _is_nollan(self, server, nick):
        if self.wrapper.find_gamble_with_nick(nick):
            return False
        else:
            return True

    def new_join(self, server, source_nick, channel):
        if self._is_nollan(server, source_nick):
            self.plugin.voice(server, source_nick, channel)
            is_new = self._check_if_new_and_if_so_add(server, source_nick)
            self._notify_subscribers(server, source_nick, is_new)

    def person_devoiced(self, server, nick):
        logging.info('person devoiced: ' + nick)
        self.wrapper.set_nollan_fake(nick)
        self.wrapper.add_gamble(nick)

    def person_voiced(self, server, nick):
        self.wrapper.add_nollan(Nollan(nick=nick))
        self.wrapper.remove_gamble_with_nick(nick)

    def voice_previously_unvoiced_nollan(self, server, channel):
        logging.info('_voice_previously_unvoiced_nollan ' + channel)
        self.plugin.channels_pending_user_for_voicing.append(channel)
        self.plugin.names(server, channel)

    def nicks_received(self, server, channel, nicks):
        for nick in nicks:
            if nick != self.plugin.nick and self._is_nollan(server, nick):
                self.plugin.voice(server, nick, channel)

    def voice_nollan(self, server, channel, nick):
        self.plugin.voice(server, nick, channel)
        self.wrapper.remove_gamble_with_nick(nick)
        nollan = self.wrapper.find_nollan_with_nick(nick)
        if not nollan:
            self.wrapper.add_nollan(Nollan(nick=nick))

    def devoice_gamble(self, server, channel, nick):
        self.plugin.devoice(server, nick, channel)
        self.wrapper.set_nollan_fake(nick)
        self.wrapper.add_gamble(nick)


    def _notify_subscribers(self, server, nick, is_new):
        subscriber_status = Subscriber.ON if is_new else Subscriber.ALL
        subscribers = self.wrapper.find_subscribers_with_status(subscriber_status)
        msg = nick + ' joined.'
        for subscriber in subscribers:
            self._notify(server, subscriber, msg)
            logging.info(msg + ' sent to ' + subscriber.nick)

    def _notify(self, server, subscriber, msg):
        if Subscriber.QUERY in subscriber.modes:
            self.plugin.privmsg(server, subscriber.nick, msg)

    def _check_if_new_and_if_so_add(self, server, nick):
        if not self.wrapper.find_nollan_with_nick(nick):
            self.wrapper.add_nollan(Nollan(nick=nick))
            return True
        else:
            return False

    def subscribe_status(self, server, source, target, command):
        target_nick = self.plugin.nick_extract(source)
        available = Subscriber.available_statuses()
        if command in available:
            self.wrapper.subscribe_status(target_nick, command)
            self.plugin.privmsg(server, target_nick, 'Subscription status set to ' + command)
        else:
            self.plugin.privmsg(server, target_nick,
                         'Invalid mode, only one the following are available: ' + ','.join(available))

    def subscribe_mode(self, server, source, target, command):
        target_nick = self.plugin.nick_extract(source)
        available = Subscriber.available_modes()
        parts = [p.strip() for p in command.split(' ')]
        error_msg = 'Invalid command: should be add/remove [mode] where mode is ' + ','.join(available)
        if len(parts) != 2:
            self.plugin.privmsg(server, target_nick, error_msg)
        else:
            [op, mode] = parts
            if mode in available and op in ['add', 'remove']:
                subscriber = self.wrapper.subscribe_mode(target_nick, op, mode)
                self.plugin.privmsg(server, target_nick, 'Updated modes, now: ' + str(subscriber.modes))
            else:
                self.plugin.privmsg(server, target_nick, error_msg)

    def send_help(self, server, source, target, query):
        target_nick = self.plugin.nick_extract(source)
        self.plugin.privmsg(server, target_nick, 'derpiherp')
