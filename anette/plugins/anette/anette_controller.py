import logging
from datetime import datetime
from nollan import Nollan
from subscriber import Subscriber


class AnetteController(object):

    def __init__(self, plugin, wrapper, server):
        self.plugin = plugin
        self.wrapper = wrapper
        self.server = server

    def _is_nollan(self, server, nick):
        if self.wrapper.find_gamble_with_nick(nick):
            return False
        else:
            return True

    def is_gamble(self, nick):
        if self.wrapper.find_gamble_with_nick(nick):
            return True
        else:
            return False

    def new_join(self, server, source_nick, channel):
        if self._is_nollan(server, source_nick):
            self.plugin.voice(server, source_nick, channel)
            is_new = self._check_if_new_and_if_so_add(server, source_nick)
            self._notify_subscribers(server, channel, source_nick, is_new)

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

    def voice_nollan(self, nick):
        channels = self.plugin.channels_watching.get(self.server, [])

        for c in channels:
            logging.info('voicing '+nick+' in '+c)
            self.plugin.voice(self.server, nick, c)
            self.wrapper.remove_gamble_with_nick(nick)
            nollan = self.wrapper.find_nollan_with_nick(nick)
            if not nollan:
                self.wrapper.add_nollan(Nollan(nick=nick))

    def devoice_gamble(self, nick):
        channels = self.plugin.channels_watching.get(self.server, [])
        for c in channels:
            logging.info('devoicing '+nick+' in '+c)
            self.plugin.devoice(self.server, nick, c)
            self.wrapper.set_nollan_fake(nick)
            self.wrapper.add_gamble(nick)

    def _notify_subscribers(self, server, channel, nick, is_new):
        subscriber_statuses = [Subscriber.ON, Subscriber.ALL] if is_new else [Subscriber.ALL]
        subscribers = self.wrapper.find_subscribers_with_statuses(subscriber_statuses)
        msg = nick + ' joined ' + channel
        self._send_pushbullet_notificaiton(server, msg, is_new)
        for subscriber in subscribers:
            self._notify(server, subscriber, msg)
            logging.info('"' + msg + '" sent to ' + subscriber.nick)

    def _notify(self, server, subscriber, msg):
        if Subscriber.QUERY in subscriber.modes:
            self.plugin.privmsg(server, subscriber.nick, msg)

    def _send_pushbullet_notificaiton(self, server, msg, is_new):
        pb = self.plugin.pushbullets.get(server)
        if is_new:
            pb.push_to_tag('anette_new', msg, datetime.now().isoformat())

        pb.push_to_tag('anette_all', msg, datetime.now().isoformat())

    def _check_if_new_and_if_so_add(self, server, nick):
        if not self.wrapper.find_nollan_with_nick(nick):
            self.wrapper.add_nollan(Nollan(nick=nick))
            return True
        else:
            return False

    # commands below

    def subscribe_status(self, server, source, target, command):
        target_nick = self.plugin.nick_extract(source)
        available = Subscriber.available_statuses()
        if not command:
            subscriber = self.wrapper.find_subscriber_with_nick(self.plugin.nick_extract(source))
            if subscriber:
                self.plugin.privmsg(server, target_nick, 'current status: '\
                                    + Subscriber.status_from_int(subscriber.status))
            else:
                self.plugin.privmsg(server, target_nick, 'no subscription')
        elif command in available:
            self.wrapper.subscribe_status(target_nick, command)
            self.plugin.privmsg(server, target_nick, 'subscription status set to ' + command)
        else:
            self.plugin.privmsg(server, target_nick, 'invalid command')

    def subscribe_mode(self, server, source, target, command):
        target_nick = self.plugin.nick_extract(source)
        available = Subscriber.available_modes()
        parts = [p.strip() for p in command.split(' ')]
        error_msg = 'invalid command'
        if not parts:
            subscriber = self.wrapper.find_subscriber_with_nick(target_nick)
            if subscriber:
                self.plugin.privmsg(server, target_nick, 'current modes: ' + str(subscriber.modes))
            else:
                self.plugin.privmsg(server, target_nick, 'no subscription')
        elif len(parts) == 2:
            [op, mode] = parts
            if mode in available and op in ['add', 'remove']:
                subscriber = self.wrapper.subscribe_mode(target_nick, op, mode)
                self.plugin.privmsg(server, target_nick, 'updated modes, now: ' + str(subscriber.modes))
            else:
                self.plugin.privmsg(server, target_nick, error_msg)
        else:
            self.plugin.privmsg(server, target_nick, error_msg)

    def join_channel(self, server, source, chan):
        parts = [p.strip() for p in chan.split(' ')]
        if len(parts) != 1 or not chan.startswith('#'):
            self.plugin.privmsg(server, self.plugin.nick_extract(source), 'no such channel: ' + chan)
        else:
            if chan not in self.plugin.channels_watching[server]:
                self.plugin.channels_watching[server].append(chan)
            logging.info('channels to watch: ' + str(self.plugin.channels_watching[server]))
            self.plugin.join(server, chan)

    def send_help(self, server, source, target, is_admin, command):
        target_nick = self.plugin.nick_extract(source)
        if not command:
            self.plugin.privmsg(server, target_nick, 'subscribe status [off|on|all]')
            if is_admin:
                self.plugin.privmsg(server, target_nick, 'voice <nick>')
                self.plugin.privmsg(server, target_nick, 'devoice <nick>')
                self.plugin.privmsg(server, target_nick, 'join <channel>')
        elif command == 'subscribe' or command == 'subscribe status':
            self.plugin.privmsg(server, target_nick, 'subscribe status [off|on|all]')
            self.plugin.privmsg(server, target_nick, 'off = no subscription')
            self.plugin.privmsg(server, target_nick, 'on  = ping first time nollan joins')
            self.plugin.privmsg(server, target_nick, 'all = ping every time nollan joins')
            self.plugin.privmsg(server, target_nick, 'leave empty for current status')
