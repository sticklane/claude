'use strict';

const fs = require('fs');
const path = require('path');
const { parsePost } = require('./src/meta');
const { renderPost } = require('./src/render');
const { buildFeed } = require('./src/feed');
const { buildArchive } = require('./src/archive');

const POSTS_DIR = path.join(__dirname, 'posts');
const OUT_DIR = process.env.OUT_DIR || path.join(__dirname, 'out');

function loadPosts() {
  return fs.readdirSync(POSTS_DIR)
    .filter((f) => f.endsWith('.md'))
    .map((f) => parsePost(fs.readFileSync(path.join(POSTS_DIR, f), 'utf8')))
    // Newest first; ISO date strings sort lexicographically.
    .sort((a, b) => (a.date < b.date ? 1 : a.date > b.date ? -1 : 0));
}

function build(outDir = OUT_DIR) {
  const posts = loadPosts();
  fs.rmSync(outDir, { recursive: true, force: true });
  fs.mkdirSync(path.join(outDir, 'posts'), { recursive: true });
  for (const post of posts) {
    fs.writeFileSync(path.join(outDir, 'posts', `${post.slug}.html`), renderPost(post));
  }
  fs.writeFileSync(path.join(outDir, 'index.html'), buildArchive(posts));
  fs.writeFileSync(path.join(outDir, 'feed.xml'), buildFeed(posts));
  return outDir;
}

if (require.main === module) {
  const out = build();
  process.stdout.write(`built sample site to ${out}\n`);
}

module.exports = { build, loadPosts };
