'use strict';

const { formatDate } = require('./date');

// Parses a post's front matter and builds its <head> metadata block.
// Date formatting is delegated to the shared src/date.js module.

function parsePost(raw) {
  const match = raw.match(/^---\n([\s\S]*?)\n---\n?([\s\S]*)$/);
  if (!match) throw new Error('post is missing a front-matter block');
  const meta = {};
  for (const line of match[1].split('\n')) {
    const idx = line.indexOf(':');
    if (idx === -1) continue;
    meta[line.slice(0, idx).trim()] = line.slice(idx + 1).trim();
  }
  return {
    title: meta.title,
    date: meta.date,
    slug: meta.slug,
    body: match[2].trim(),
  };
}

function buildMeta(post) {
  return `<meta name="published" content="${formatDate(post.date)}">`;
}

module.exports = { parsePost, buildMeta, formatDate };
