module.exports = {
  valueToKey: function (obj, value, property) {
    for (var i in obj) {
      if ((property && obj[i] && obj[i][property] == value) ||
        (!property && obj[property] == value)) {
        return i;
      }
    }

    return i;
  },

  copy: function (obj) {
    return obj ? JSON.parse(JSON.stringify(obj)) : false;
  }
};