var events = require('events');
var util = require('util');
var utils = require('./utils');

var DataStore = function (options) {
  this.data = {};
  this.verbose = options.verbose;

  if (this.verbose) {
    console.log('Created a new DataStore');
  }

  events.EventEmitter.call(this);
};

util.inherits(DataStore, events.EventEmitter);

DataStore.prototype.set = function (key, value) {
  var oldValue = utils.copy(this.data[key]);
  this.data[key] = value;

  this.emit(key, value, oldValue);
  console.log('DataStore.set => ' + key);
};

DataStore.prototype.get = function (key, defaultValue) {
  return this.data[key];
};

module.exports = DataStore;