'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const { formatDate } = require('../src/date');
const { buildArchive } = require('../src/archive');

// Regression coverage for the drift bug: December dates formatted to
// "undefined" before the duplicated formatters were unified.

test('formatDate renders December correctly', () => {
  assert.equal(formatDate('2023-12-25'), 'December 25, 2023');
});

test('formatDate covers every month boundary', () => {
  assert.equal(formatDate('2023-01-01'), 'January 1, 2023');
  assert.equal(formatDate('2023-11-30'), 'November 30, 2023');
  assert.equal(formatDate('2023-12-31'), 'December 31, 2023');
});

test('buildArchive renders a December post with the correct month', () => {
  const html = buildArchive([{ title: 'Year End', date: '2023-12-25', slug: 'year-end' }]);
  assert.match(html, /Year End<\/a> — December 25, 2023/);
  assert.doesNotMatch(html, /undefined/);
});
