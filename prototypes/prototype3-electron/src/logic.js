/**
 * src/logic.js
 * Pure business logic for Gertrude Shell.
 * No Electron dependencies — fully testable with Jest in Node.js.
 */

'use strict';

const fs = require('fs');

// ─── Constants ────────────────────────────────────────────────────────────────

/**
 * Whitelisted domains. A URL is safe if its hostname ends with one of these
 * (e.g. "www.facebook.com" ends with "facebook.com" → safe).
 */
const WHITELIST_DOMAINS = [
  'facebook.com',
  'photos.google.com',
  'google.com',
  'aol.com',
  'mail.aol.com',
  'accounts.google.com',
  'ssl.gstatic.com',
];

/**
 * App definitions. Each entry describes one button on the main board.
 * Non-desktop apps have a `url`; Desktop has `action: 'desktop'`.
 */
const APPS = [
  {
    id: 'facebook',
    label: 'Facebook',
    url: 'https://www.facebook.com',
    icon: '👤',
    color: '#1877F2',
    textColor: '#ffffff',
  },
  {
    id: 'milo',
    label: 'Milo\n(Photos)',
    displayName: 'Milo (Google Photos)',
    url: 'https://photos.google.com',
    icon: '📸',
    color: '#4285F4',
    textColor: '#ffffff',
  },
  {
    id: 'aolnews',
    label: 'AOL News',
    url: 'https://www.aol.com',
    icon: '📰',
    color: '#FF0B00',
    textColor: '#ffffff',
  },
  {
    id: 'aolmail',
    label: 'AOL Mail',
    url: 'https://mail.aol.com',
    icon: '✉️',
    color: '#FF0B00',
    textColor: '#ffffff',
  },
  {
    id: 'desktop',
    label: 'Desktop',
    action: 'desktop',
    icon: '🖥️',
    color: '#5C6BC0',
    textColor: '#ffffff',
  },
];

/**
 * Default configuration returned when no config file exists yet.
 */
const DEFAULT_CONFIG = {
  setupComplete: false,
  firstRun: true,
  userName: 'Gertrude',
  credentials: {
    facebook: { username: '', password: '' },
    aolmail: { username: '', password: '' },
  },
};

// ─── Pure Functions ────────────────────────────────────────────────────────────

/**
 * Returns a time-appropriate greeting for Gertrude.
 *
 * Morning:   05:00 – 11:59
 * Afternoon: 12:00 – 17:59
 * Evening:   18:00 – 04:59 (wraps through midnight)
 *
 * @param {number} hour - Hour of day (0–23, integer)
 * @returns {string}
 */
function getGreeting(hour) {
  if (hour >= 5 && hour < 12) {
    return 'Good Morning, Gertrude!';
  } else if (hour >= 12 && hour < 18) {
    return 'Good Afternoon, Gertrude!';
  } else {
    return 'Good Evening, Gertrude!';
  }
}

/**
 * Returns true if the given URL string is within the whitelisted domains.
 * Only http:// and https:// protocols are allowed.
 *
 * @param {string|null|undefined} url
 * @returns {boolean}
 */
function isSafeUrl(url) {
  if (!url || typeof url !== 'string' || url.trim() === '') {
    return false;
  }

  let parsed;
  try {
    parsed = new URL(url);
  } catch (_) {
    return false;
  }

  // Only allow http and https
  if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
    return false;
  }

  const hostname = parsed.hostname.toLowerCase();

  // Check if hostname matches or ends with any whitelisted domain
  return WHITELIST_DOMAINS.some(domain => {
    return hostname === domain || hostname.endsWith('.' + domain);
  });
}

/**
 * Returns a friendly display name for a URL, matching known apps first,
 * then falling back to the hostname, or empty string for invalid URLs.
 *
 * @param {string|null|undefined} url
 * @returns {string}
 */
function getAppDisplayName(url) {
  if (!url || typeof url !== 'string' || url.trim() === '') {
    return '';
  }

  let parsed;
  try {
    parsed = new URL(url);
  } catch (_) {
    return '';
  }

  const hostname = parsed.hostname.toLowerCase();

  // Match exact app URLs first
  if (hostname === 'www.facebook.com' || hostname === 'facebook.com') {
    return 'Facebook';
  }
  if (hostname === 'photos.google.com') {
    return 'Milo (Google Photos)';
  }
  if (hostname === 'mail.aol.com') {
    return 'AOL Mail';
  }
  if (hostname === 'www.aol.com' || hostname === 'aol.com') {
    return 'AOL News';
  }
  if (hostname === 'accounts.google.com') {
    return 'Google Sign-In';
  }

  // Fall back to hostname
  return hostname;
}

/**
 * Loads a JSON config from the given file path.
 * Returns DEFAULT_CONFIG if the file does not exist or cannot be parsed.
 *
 * @param {string} filePath - Absolute path to the config JSON file
 * @returns {object}
 */
function loadConfig(filePath) {
  try {
    if (!fs.existsSync(filePath)) {
      return { ...DEFAULT_CONFIG };
    }
    const raw = fs.readFileSync(filePath, 'utf8');
    return JSON.parse(raw);
  } catch (_) {
    return { ...DEFAULT_CONFIG };
  }
}

/**
 * Saves a config object as JSON to the given file path.
 * Creates the file (and parent directories) if they do not exist.
 *
 * @param {string} filePath - Absolute path to write the config JSON
 * @param {object} config   - Config object to serialise
 */
function saveConfig(filePath, config) {
  const dir = require('path').dirname(filePath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  fs.writeFileSync(filePath, JSON.stringify(config, null, 2), 'utf8');
}

// ─── Exports ──────────────────────────────────────────────────────────────────

module.exports = {
  getGreeting,
  isSafeUrl,
  getAppDisplayName,
  loadConfig,
  saveConfig,
  DEFAULT_CONFIG,
  WHITELIST_DOMAINS,
  APPS,
};
