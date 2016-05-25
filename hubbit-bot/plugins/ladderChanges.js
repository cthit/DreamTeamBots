var utils = require('../libs/utils');

module.exports = function (pluginManager, config) {
  var manager = pluginManager.getShared('RequestManager');
  var bot = pluginManager.getShared('IrcBot');
  var memory = pluginManager.getShared('DataStore');

  manager.on('request', function (response) {
    var ladderChanges = [];
    var newUsers = {};
    var users = memory.get('previousStats') || {};
    var data;

    try {
      data = JSON.parse(response);
    } catch (error) {
      bot.say('jeeppson jag har kraschat, hjälp!');
      return console.error('Failed to parse JSON (invalid auth token?)');
    }

    for (var i in data) {
      // Check if the old position differs from the new position
      if (users && users[data[i].user_id] && users[data[i].user_id].position != i) {
        ladderChanges.push({
          from: users[data[i].user_id].position,
          to: i,
          totalTime: data[i].total_time,
          nick: data[i].nick
        });
      }

      // Change the position in the store
      newUsers[data[i].user_id] = {
        position: i,
        active: data[i].active,
        nick: data[i].nick
      };
    }

    memory.set('previousStats', newUsers);
    memory.set('ladderChanges', ladderChanges);
  });

  memory.on('ladderChanges', function (value, oldValue) {
    if (!value) return;

    var users = memory.get('previousStats');

    value.forEach(function (entry) {
      // From position
      var other = utils.valueToKey(users, entry.from, 'position');

      // To position
      var you = utils.valueToKey(users, entry.to, 'position');

      // If both are active they probably haven't changed position
      if (users[you].active && users[other].active) {
        return;
      }

      entry.from = parseInt(entry.from);
      entry.to = parseInt(entry.to);

      if (entry.from > entry.to) {
        var hours = Math.floor(entry.totalTime / (60 * 60));
        var positionFrom = entry.from + 1;
        var positionTo = entry.to + 1;

        var yourNick = users[you].nick;
        var othersNick = users[other].nick;

        bot.say(yourNick + " passed " + othersNick + " (from #" + positionFrom + " to #" + positionTo + " - " + hours + "h).");
      }
    });
  });
};