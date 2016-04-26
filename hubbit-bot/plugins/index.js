var PluginManager = function () {
  this.plugins = {};
  this.shared = {};
};

PluginManager.prototype.load = function (name, config) {
  this.plugins[name] = require('./' + name)(this, config);
};

PluginManager.prototype.getShared = function (key) {
  return this.shared[key];
};

PluginManager.prototype.setShared = function (key, value) {
  this.shared[key] = value;
};

PluginManager.prototype.getPlugin = function (name) {
  return this.plugins[name];
};

module.exports = new PluginManager();