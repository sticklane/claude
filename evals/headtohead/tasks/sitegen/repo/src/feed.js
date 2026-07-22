'use strict';

// NOTE: date-formatting logic below is intentionally duplicated across
// src/meta.js, src/render.js, src/archive.js, and here.

function formatDate(iso) {
  const [y, m, d] = iso.split('-').map(Number);
  const MONTHS = ['', 'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'];
  return `${MONTHS[m]} ${d}, ${y}`;
}

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
