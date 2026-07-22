'use strict';

const { buildMeta } = require('./meta');
const { formatDate } = require('./date');

// Date formatting is delegated to the shared src/date.js module.

function renderPost(post) {
  return [
    '<!doctype html>',
    '<html>',
    '<head>',
    buildMeta(post),
    `<title>${post.title}</title>`,
    '</head>',
    '<body>',
    '<article>',
    `<h1>${post.title}</h1>`,
    `<p class="date">${formatDate(post.date)}</p>`,
    post.body,
    '</article>',
    '</body>',
    '</html>',
    '',
  ].join('\n');
}

module.exports = { renderPost, formatDate };
