'use strict';

const { buildMeta } = require('./meta');

// NOTE: date-formatting logic below is intentionally duplicated across
// src/meta.js, src/feed.js, src/archive.js, and here.

function formatDate(iso) {
  const [y, m, d] = iso.split('-').map(Number);
  const MONTHS = ['', 'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'];
  return `${MONTHS[m]} ${d}, ${y}`;
}

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
