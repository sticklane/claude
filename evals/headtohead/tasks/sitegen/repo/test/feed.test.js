'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const { buildFeed, formatDate } = require('../src/feed');

const POSTS = [
  { title: 'Spring Notes', date: '2023-04-20', slug: 'spring-notes' },
  { title: 'Hello World', date: '2023-01-05', slug: 'hello-world' },
];

test('buildFeed emits one <item> per post', () => {
  const xml = buildFeed(POSTS);
  assert.equal((xml.match(/<item>/g) || []).length, 2);
});

test('buildFeed formats each item date', () => {
  const xml = buildFeed(POSTS);
  assert.match(xml, /<date>April 20, 2023<\/date>/);
  assert.match(xml, /<date>January 5, 2023<\/date>/);
});

test('formatDate renders a non-padded human date', () => {
  assert.equal(formatDate('2023-04-20'), 'April 20, 2023');
});
