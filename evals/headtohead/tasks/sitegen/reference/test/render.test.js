'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const { renderPost, formatDate } = require('../src/render');

const POST = { title: 'Hello World', date: '2023-01-05', slug: 'hello-world', body: '<p>Body.</p>' };

test('renderPost includes the title in an <h1> and the body', () => {
  const html = renderPost(POST);
  assert.match(html, /<h1>Hello World<\/h1>/);
  assert.match(html, /<p>Body\.<\/p>/);
});

test('renderPost shows the formatted post date', () => {
  const html = renderPost(POST);
  assert.match(html, /<p class="date">January 5, 2023<\/p>/);
});

test('formatDate renders a non-padded human date', () => {
  assert.equal(formatDate('2023-04-20'), 'April 20, 2023');
});
