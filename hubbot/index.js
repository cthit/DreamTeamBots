var irc = require('irc');
var config = require('./config.js').irc;

var client = new irc.Client(config.server, config.nick, {
    userName: config.userName,
    port: config.port,
    debug: config.debug,
    secure: config.secure
});

require('./queryPresent.js')(client);

client.addListener('error', (error) => {
    console.log(error);
});