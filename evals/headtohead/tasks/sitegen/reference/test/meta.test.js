'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const { parsePost, buildMeta, formatDate } = require('../src/meta');

const RAW = '---\ntitle: Hello World\ndate: 2023-01-05\nslug: hello-world\n---\n<p>Body.</p>\n';

test('parsePost extracts title, date, slug, and body', () => {
  const post = parsePost(RAW);
  assert.equal(post.title, 'Hello World');
  assert.equal(post.date, '2023-01-05');
  assert.equal(post.slug, 'hello-world');
  assert.equal(post.body, '<p>Body.</p>');
});

test('parsePost throws when the front-matter block is missing', () => {
  assert.throws(() => parsePost('no front matter here'));
});

test('formatDate renders a non-padded human date', () => {
  assert.equal(formatDate('2023-01-05'), 'January 5, 2023');
  assert.equal(formatDate('2023-04-20'), 'April 20, 2023');
});

test('buildMeta embeds the formatted published date', () => {
  const meta = buildMeta({ date: '2023-04-20' });
  assert.match(meta, /name="published"/);
  assert.match(meta, /content="April 20, 2023"/);
});
