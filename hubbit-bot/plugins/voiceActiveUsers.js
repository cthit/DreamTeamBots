module.exports = function (pluginManager, config) {
  var bot = pluginManager.getShared('IrcBot');
  var memory = pluginManager.getShared('DataStore');

  memory.on('previousStats', function (newData, oldData) {
    bot.getChannelUsers(function (ircUsers) {
      if (!ircUsers) return;

      for (var nickname in newData) {
        if (newData[nickname].active && ircUsers[nickname] === false) {
          bot.setPermission('#hubbit', '+v', nickname);
        } else if (!newData[nickname].active && ircUsers[nickname] === true) {
          bot.setPermission('#hubbit', '-v', nickname);
        }
      }
    });
  });
};