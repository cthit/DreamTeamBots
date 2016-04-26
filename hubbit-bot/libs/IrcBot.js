var irc = require('irc');

var IrcBot = function (options) {
  this.nickname = options.nickname;
  this.username = options.username;
  this.channel = options.channel;

  if (options.dummy) {
    console.log('Joined ' + this.channel + ' on Dummy IRC server as ' + options.nickname);

    // Create a dummy object
    this.client = {
      say: function (channel, message) {
        console.log('IrcBot.say (' + channel + ') => ' + message);
      },
      send: function (message) {
        console.log('IrcBot.send => ' + message);
      },
      addListener: function () {}
    };
  } else {
    // Connect to IRC
    this.client = new irc.Client(options.server, options.nickname, {
      port: options.port,
      debug: options.debug,
      secure: options.secure,
      userName: options.username,
      password: options.password,
      realName: options.nickname,
      channels: [options.channel]
    });

    if (options.password) {
      setTimeout(() => {
        console.log('Signed in with password');
        this.client.say('NickServ', 'IDENTIFY ' + options.password);
      }, 5000);
    }

    this.client.on('error', function (error) {
      console.error(error);
    });
  }
};

IrcBot.prototype.setPermission = function (channel, permission, nickname) {
  this.client.send('MODE', channel, permission, nickname);
};

IrcBot.prototype.sendRaw = function (message) {
  this.client.send(message);
};

IrcBot.prototype.say = function (message) {
  this.client.say(this.channel, message);
};

IrcBot.prototype.getChannelUsers = function (callback) {
  var nickname = this.nickname;

  var stopListener = () => {
    this.client.removeListener('message', handleMessage);
  };

  var handleMessage = function (data) {
    if (data.command == 'rpl_namreply' && data.commandType == 'reply') {
      stopListener();
      var allUsers = data.args[3].split(' ');

      var users = {};
      var cleanName;

      for (var i in allUsers) {
        if (allUsers[i] && allUsers[i] != nickname) {
          cleanName = allUsers[i].replace(/(\+)|(\~)|(\%)|(\&)/, '');
          users[cleanName] = /\+/.test(allUsers[i]);
        }
      }

      if (!users.length) return;

      callback(users);
    }
  };

  this.client.addListener('raw', handleMessage);
  this.client.send('NAMES', '#hubbit');
};

module.exports = IrcBot;