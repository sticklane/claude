'use strict';

// Single shared date-formatting module. Every call site (meta, render,
// feed, archive) imports formatDate from here — the previously duplicated,
// drifted copies were unified into this one correct definition.

const MONTHS = ['', 'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'];

function formatDate(iso) {
  const [y, m, d] = iso.split('-').map(Number);
  return `${MONTHS[m]} ${d}, ${y}`;
}

module.exports = { formatDate };
