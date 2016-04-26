var request = require('request');
var events = require('events');
var util = require('util');
var fs = require('fs');

var RequestManager = function (options) {
  this.interval = options.interval;
  this.verbose = options.verbose;
  this.dummy = options.dummy;
  this.dummyDataId = 1;

  this.options = {
    url: options.url,
    headers: options.headers
  };

  if (this.verbose) {
    this.on('error', function(err) {
      console.log(err);
    });
  }

  events.EventEmitter.call(this);
};

util.inherits(RequestManager, events.EventEmitter);

RequestManager.prototype.request = function () {
  if (this.verbose) {
    process.stdout.write('Requesting ' + this.options.url + '... ');
  }

  if (this.dummy) {
    console.log('dummy data ./test/' + this.dummyDataId + '.json');

    setTimeout(() => {
      var body = fs.readFileSync(__dirname + '/../test/' + this.dummyDataId + '.json', 'utf8');
      this.emit('request', body);
      this.dummyDataId = this.dummyDataId == 1 ? 2 : 1;
    }, 200);

    return;
  }

  request(this.options, (err, response, body) => {
    if (this.verbose && response && response.statusCode) {
      console.log(response.statusCode);
    }

    if (err) {
      return this.emit('error', err);
    }

    this.emit('request', body);
  });
};

RequestManager.prototype.start = function () {
  if (this.verbose) {
    console.log('Started ' + (this.interval / 1000) + 's interval');
  }

  // Start calling request on a specific interval
  this.intervalObject = setInterval(() => { this.request(); }, this.interval);

  // Run it immediately as well
  //this.request();
};

RequestManager.prototype.stop = function () {
  clearInterval(this.intervalObject);
};

module.exports = RequestManager;