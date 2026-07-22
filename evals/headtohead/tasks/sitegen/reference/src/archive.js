'use strict';

const { formatDate } = require('./date');

// Date formatting is delegated to the shared src/date.js module. The drifted
// copy that rendered December dates as "undefined" is gone; all call sites
// now share the one correct definition.

function buildArchive(posts) {
  const rows = posts.map((post) =>
    `<li><a href="posts/${post.slug}.html">${post.title}</a> — ${formatDate(post.date)}</li>`);
  return [
    '<!doctype html>',
    '<html>',
    '<head><title>Archive</title></head>',
    '<body>',
    '<ul>',
    ...rows,
    '</ul>',
    '</body>',
    '</html>',
    '',
  ].join('\n');
}

module.exports = { buildArchive, formatDate };
