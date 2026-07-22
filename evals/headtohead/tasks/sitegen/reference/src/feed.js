'use strict';

const { formatDate } = require('./date');

// Date formatting is delegated to the shared src/date.js module.

function buildFeed(posts) {
  const items = posts.map((post) => [
    '  <item>',
    `    <title>${post.title}</title>`,
    `    <date>${formatDate(post.date)}</date>`,
    '  </item>',
  ].join('\n'));
  return [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<feed>',
    ...items,
    '</feed>',
    '',
  ].join('\n');
}

module.exports = { buildFeed, formatDate };
