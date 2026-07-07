/* Reads a JSON array of [material, treatment, params, route] cases on stdin,
 * runs each through the browser guardrail (docs/guardrail.js), and writes the
 * array of verdict statuses to stdout. Used by tests/parity.py. */
'use strict';
var path = require('path');
var G = require(path.join(__dirname, '..', 'docs', 'guardrail.js'));
var input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', function (d) { input += d; });
process.stdin.on('end', function () {
  var cases = JSON.parse(input);
  var out = cases.map(function (c) { return G.assess(c[0], c[1], c[2], c[3]).status; });
  process.stdout.write(JSON.stringify(out));
});
