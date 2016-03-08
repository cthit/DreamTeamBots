var request = require('request');
var config = require('./config.js');

module.exports = function(bot) {

  bot.addListener('pm', (from, message) => {
    if (message.startsWith("hubbis")) {
      var nicks = message.split(' ').slice(1)

      console.log("querying for:", nicks);

      var options = {
        url: config.hubbit_url,
        headers: {
          Authorization: "Token " + config.token
        }
      }

      request(options, (error, response, body) => {
        if (!error && response.statusCode == 200) {
          var json = JSON.parse(body);
          var filteredUsers = json.filter((user) => nicks.some((nick) => nick.toLowerCase() === user.nick.toLowerCase()));

          nicks
            .filter(nick => !filteredUsers
              .some(filteredUser => nick.toLowerCase() === filteredUser.nick.toLowerCase()))
            .forEach(nick => bot.say(from, nick + ': No such user'))

          filteredUsers
            .map((user) => user.nick + ": " + (user.active ? "YUS!" : "No"))
            .forEach(msg => bot.say(from, msg));
        }
      })
    } else {
      bot.say(from, 'hubbis nick [nick...]');
    }
  });
};