const path = require('path');

module.exports = {
  entry: './bundle.js',
  output: {
    filename: 'main.js',
    path: path.resolve(__dirname, 'dist'),
  },
};