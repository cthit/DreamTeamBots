// Rename this file to config.js

module.exports = {
  // IRC connection details
  server: 'irc.chalmers.it',
  port: 9999,
  secure: true,
  channel: '#hubbit',
  nickname: 'HubbIT',
  password: '...',
  username: 'banned',

  debug: true,

  // Faux IRC client, to avoid spamming the server for testing
  ircDummy: true,

  // Dummy hubbit API data (that changes between every request, for testing)
  requestDummy: true,

  // chalmers.it cookie contents
  chalmersItAuth: 'chalmersItAuth=...; _hubbIT_session=...',

  // Refresh interval
  interval: 60 * 1000
};