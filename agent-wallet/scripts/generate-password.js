#!/usr/bin/env node
'use strict';

const { randomBytes } = require('crypto');

const UPPER = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
const LOWER = 'abcdefghijklmnopqrstuvwxyz';
const DIGITS = '0123456789';
const SPECIAL = '!@#$%^&*';
const ALL = UPPER + LOWER + DIGITS + SPECIAL;

function pick(charset) {
  return charset[randomBytes(1)[0] % charset.length];
}

function generatePassword(length = 12) {
  // Guarantee at least one of each required character class
  const required = [
    pick(UPPER),
    pick(LOWER),
    pick(DIGITS),
    pick(SPECIAL),
  ];

  const remaining = Array.from({ length: length - required.length }, () =>
    pick(ALL)
  );

  // Shuffle required + remaining together using Fisher-Yates
  const chars = [...required, ...remaining];
  for (let i = chars.length - 1; i > 0; i--) {
    const j = randomBytes(1)[0] % (i + 1);
    [chars[i], chars[j]] = [chars[j], chars[i]];
  }

  return chars.join('');
}

process.stdout.write(generatePassword());
