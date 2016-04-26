var config = require('./config');
var IrcBot = require('./libs/IrcBot');
var RequestManager = require('./libs/RequestManager');
var DataStore = require('./libs/DataStore');
var plugins = require('./plugins');

var bot = new IrcBot({
  server: config.server,
  nickname: config.nickname,
  password: config.password,
  username: config.username,
  port: config.port,
  debug: config.debug,
  channel: config.channel,
  dummy: config.ircDummy,
});

var headers = { 'Cookie': config.chalmersItAuth };

var manager = new RequestManager({
  url: 'https://hubbit.chalmers.it/stats.json',
  interval: config.interval,
  verbose: config.debug,
  headers: headers,
  dummy: config.requestDummy
});

var memory = new DataStore({
  verbose: config.debug
});

// Expose objects to plugins
plugins.setShared('IrcBot', bot);
plugins.setShared('RequestManager', manager);
plugins.setShared('DataStore', memory);

// Load all plugins
plugins.load('ladderChanges');
plugins.load('voiceActiveUsers');

// Start sending request interval
manager.start();