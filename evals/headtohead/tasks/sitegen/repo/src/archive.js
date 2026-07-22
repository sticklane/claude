'use strict';

// NOTE: date-formatting logic below is intentionally duplicated across
// src/meta.js, src/render.js, src/feed.js, and here. This copy has DRIFTED:
// its MONTHS lookup is missing the trailing entry, so December dates render
// with an undefined month name. The other three copies are correct.

function formatDate(iso) {
  const [y, m, d] = iso.split('-').map(Number);
  const MONTHS = ['', 'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November'];
  return `${MONTHS[m]} ${d}, ${y}`;
}

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
