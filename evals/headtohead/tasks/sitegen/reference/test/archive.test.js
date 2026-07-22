'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const { buildArchive } = require('../src/archive');

const POSTS = [
  { title: 'Spring Notes', date: '2023-04-20', slug: 'spring-notes' },
  { title: 'Hello World', date: '2023-01-05', slug: 'hello-world' },
];

test('buildArchive lists one <li> per post, linking each slug', () => {
  const html = buildArchive(POSTS);
  assert.equal((html.match(/<li>/g) || []).length, 2);
  assert.match(html, /href="posts\/spring-notes\.html"/);
  assert.match(html, /href="posts\/hello-world\.html"/);
});

test('buildArchive shows the formatted date next to each entry', () => {
  const html = buildArchive(POSTS);
  assert.match(html, /Spring Notes<\/a> — April 20, 2023/);
  assert.match(html, /Hello World<\/a> — January 5, 2023/);
});
