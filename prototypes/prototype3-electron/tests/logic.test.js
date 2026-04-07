/**
 * tests/logic.test.js
 * TDD Unit Tests for Gertrude Shell Logic (RED phase - written first)
 *
 * Run with: npm test
 */

const path = require('path');
const os = require('os');
const fs = require('fs');

// We require the logic module which we will write next
const {
  getGreeting,
  isSafeUrl,
  getAppDisplayName,
  loadConfig,
  saveConfig,
  DEFAULT_CONFIG,
  WHITELIST_DOMAINS,
  APPS,
} = require('../src/logic');

// ─── getGreeting ───────────────────────────────────────────────────────────────

describe('getGreeting(hour)', () => {
  test('returns Good Morning for hour 5', () => {
    expect(getGreeting(5)).toBe('Good Morning, Gertrude!');
  });

  test('returns Good Morning for hour 11', () => {
    expect(getGreeting(11)).toBe('Good Morning, Gertrude!');
  });

  test('returns Good Afternoon for hour 12', () => {
    expect(getGreeting(12)).toBe('Good Afternoon, Gertrude!');
  });

  test('returns Good Afternoon for hour 17', () => {
    expect(getGreeting(17)).toBe('Good Afternoon, Gertrude!');
  });

  test('returns Good Evening for hour 18', () => {
    expect(getGreeting(18)).toBe('Good Evening, Gertrude!');
  });

  test('returns Good Evening for hour 22', () => {
    expect(getGreeting(22)).toBe('Good Evening, Gertrude!');
  });

  test('returns Good Evening for midnight (hour 0)', () => {
    expect(getGreeting(0)).toBe('Good Evening, Gertrude!');
  });

  test('returns Good Evening for hour 4', () => {
    expect(getGreeting(4)).toBe('Good Evening, Gertrude!');
  });

  test('returns Good Morning at exactly 5am', () => {
    expect(getGreeting(5)).toMatch(/Good Morning/);
  });

  test('returns a string containing "Gertrude" always', () => {
    for (let h = 0; h < 24; h++) {
      expect(getGreeting(h)).toContain('Gertrude');
    }
  });
});

// ─── isSafeUrl ─────────────────────────────────────────────────────────────────

describe('isSafeUrl(url)', () => {
  // Whitelisted domains
  test('allows facebook.com', () => {
    expect(isSafeUrl('https://www.facebook.com')).toBe(true);
  });

  test('allows facebook.com subpages', () => {
    expect(isSafeUrl('https://www.facebook.com/login')).toBe(true);
  });

  test('allows photos.google.com', () => {
    expect(isSafeUrl('https://photos.google.com')).toBe(true);
  });

  test('allows google.com (for auth)', () => {
    expect(isSafeUrl('https://google.com')).toBe(true);
  });

  test('allows accounts.google.com (for login)', () => {
    expect(isSafeUrl('https://accounts.google.com/signin')).toBe(true);
  });

  test('allows aol.com', () => {
    expect(isSafeUrl('https://www.aol.com')).toBe(true);
  });

  test('allows mail.aol.com', () => {
    expect(isSafeUrl('https://mail.aol.com')).toBe(true);
  });

  test('allows ssl.gstatic.com (Google assets)', () => {
    expect(isSafeUrl('https://ssl.gstatic.com/something')).toBe(true);
  });

  // Blocked domains
  test('blocks google.co.uk (not in whitelist)', () => {
    expect(isSafeUrl('https://www.google.co.uk')).toBe(false);
  });

  test('blocks amazon.com', () => {
    expect(isSafeUrl('https://www.amazon.com')).toBe(false);
  });

  test('blocks evil-facebook.com (domain spoofing)', () => {
    expect(isSafeUrl('https://evil-facebook.com')).toBe(false);
  });

  test('blocks notfacebook.com', () => {
    expect(isSafeUrl('https://notfacebook.com')).toBe(false);
  });

  test('blocks ftp:// protocol', () => {
    expect(isSafeUrl('ftp://facebook.com')).toBe(false);
  });

  test('returns false for empty string', () => {
    expect(isSafeUrl('')).toBe(false);
  });

  test('returns false for null', () => {
    expect(isSafeUrl(null)).toBe(false);
  });

  test('returns false for undefined', () => {
    expect(isSafeUrl(undefined)).toBe(false);
  });

  test('allows http:// protocol for whitelisted domains', () => {
    expect(isSafeUrl('http://www.facebook.com')).toBe(true);
  });

  test('blocks about:blank', () => {
    expect(isSafeUrl('about:blank')).toBe(false);
  });

  test('blocks javascript: URLs', () => {
    expect(isSafeUrl('javascript:alert(1)')).toBe(false);
  });
});

// ─── getAppDisplayName ─────────────────────────────────────────────────────────

describe('getAppDisplayName(url)', () => {
  test('returns Facebook for facebook.com URL', () => {
    expect(getAppDisplayName('https://www.facebook.com')).toBe('Facebook');
  });

  test('returns Milo (Google Photos) for photos.google.com', () => {
    expect(getAppDisplayName('https://photos.google.com')).toBe('Milo (Google Photos)');
  });

  test('returns AOL News for aol.com', () => {
    expect(getAppDisplayName('https://www.aol.com')).toBe('AOL News');
  });

  test('returns AOL Mail for mail.aol.com', () => {
    expect(getAppDisplayName('https://mail.aol.com')).toBe('AOL Mail');
  });

  test('returns Google Sign-In for accounts.google.com', () => {
    expect(getAppDisplayName('https://accounts.google.com/signin')).toBe('Google Sign-In');
  });

  test('returns the URL hostname for unknown safe URLs', () => {
    const result = getAppDisplayName('https://ssl.gstatic.com/something');
    expect(typeof result).toBe('string');
    expect(result.length).toBeGreaterThan(0);
  });

  test('returns empty string for null input', () => {
    expect(getAppDisplayName(null)).toBe('');
  });

  test('returns empty string for empty string', () => {
    expect(getAppDisplayName('')).toBe('');
  });
});

// ─── loadConfig / saveConfig ───────────────────────────────────────────────────

describe('loadConfig and saveConfig', () => {
  let tempDir;
  let tempConfigPath;

  beforeEach(() => {
    // Use a temporary directory for each test
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'gertrude-test-'));
    tempConfigPath = path.join(tempDir, 'config.json');
  });

  afterEach(() => {
    // Clean up temp files
    try {
      fs.rmSync(tempDir, { recursive: true, force: true });
    } catch (e) {
      // ignore cleanup errors
    }
  });

  test('saveConfig writes valid JSON to disk', () => {
    const config = { setupComplete: true, userName: 'Gertrude' };
    saveConfig(tempConfigPath, config);
    expect(fs.existsSync(tempConfigPath)).toBe(true);
    const raw = fs.readFileSync(tempConfigPath, 'utf8');
    const parsed = JSON.parse(raw);
    expect(parsed.setupComplete).toBe(true);
    expect(parsed.userName).toBe('Gertrude');
  });

  test('loadConfig reads config from disk', () => {
    const config = { setupComplete: true, userName: 'Gertrude', firstRun: false };
    fs.writeFileSync(tempConfigPath, JSON.stringify(config), 'utf8');
    const loaded = loadConfig(tempConfigPath);
    expect(loaded.setupComplete).toBe(true);
    expect(loaded.userName).toBe('Gertrude');
    expect(loaded.firstRun).toBe(false);
  });

  test('loadConfig returns DEFAULT_CONFIG when file does not exist', () => {
    const nonExistent = path.join(tempDir, 'nonexistent.json');
    const loaded = loadConfig(nonExistent);
    expect(loaded).toEqual(DEFAULT_CONFIG);
  });

  test('loadConfig returns DEFAULT_CONFIG when file contains invalid JSON', () => {
    fs.writeFileSync(tempConfigPath, 'NOT VALID JSON!!!', 'utf8');
    const loaded = loadConfig(tempConfigPath);
    expect(loaded).toEqual(DEFAULT_CONFIG);
  });

  test('saveConfig and loadConfig round-trip preserves all fields', () => {
    const config = {
      setupComplete: true,
      userName: 'Gertrude',
      firstRun: false,
      credentials: {
        facebook: { username: 'test@example.com', password: 'secret' },
      },
    };
    saveConfig(tempConfigPath, config);
    const loaded = loadConfig(tempConfigPath);
    expect(loaded).toEqual(config);
  });

  test('DEFAULT_CONFIG has expected shape', () => {
    expect(DEFAULT_CONFIG).toHaveProperty('setupComplete');
    expect(DEFAULT_CONFIG).toHaveProperty('userName');
    expect(DEFAULT_CONFIG).toHaveProperty('firstRun');
    expect(DEFAULT_CONFIG.setupComplete).toBe(false);
    expect(DEFAULT_CONFIG.firstRun).toBe(true);
  });
});

// ─── APPS and WHITELIST_DOMAINS constants ──────────────────────────────────────

describe('APPS constant', () => {
  test('APPS is an array', () => {
    expect(Array.isArray(APPS)).toBe(true);
  });

  test('APPS contains Facebook', () => {
    const fb = APPS.find(a => a.id === 'facebook');
    expect(fb).toBeDefined();
    expect(fb.url).toContain('facebook.com');
    expect(fb.label).toBeTruthy();
  });

  test('APPS contains Milo (Google Photos)', () => {
    const milo = APPS.find(a => a.id === 'milo');
    expect(milo).toBeDefined();
    expect(milo.url).toContain('photos.google.com');
  });

  test('APPS contains AOL News', () => {
    const news = APPS.find(a => a.id === 'aolnews');
    expect(news).toBeDefined();
    expect(news.url).toContain('aol.com');
  });

  test('APPS contains AOL Mail', () => {
    const mail = APPS.find(a => a.id === 'aolmail');
    expect(mail).toBeDefined();
    expect(mail.url).toContain('mail.aol.com');
  });

  test('APPS contains Desktop action', () => {
    const desktop = APPS.find(a => a.id === 'desktop');
    expect(desktop).toBeDefined();
    expect(desktop.action).toBe('desktop');
  });

  test('Each non-desktop app has an icon property', () => {
    APPS.filter(a => a.id !== 'desktop').forEach(app => {
      expect(app).toHaveProperty('icon');
    });
  });
});

describe('WHITELIST_DOMAINS constant', () => {
  test('WHITELIST_DOMAINS is an array', () => {
    expect(Array.isArray(WHITELIST_DOMAINS)).toBe(true);
  });

  test('WHITELIST_DOMAINS includes facebook.com', () => {
    expect(WHITELIST_DOMAINS).toContain('facebook.com');
  });

  test('WHITELIST_DOMAINS includes photos.google.com', () => {
    expect(WHITELIST_DOMAINS).toContain('photos.google.com');
  });

  test('WHITELIST_DOMAINS includes aol.com', () => {
    expect(WHITELIST_DOMAINS).toContain('aol.com');
  });

  test('WHITELIST_DOMAINS includes mail.aol.com', () => {
    expect(WHITELIST_DOMAINS).toContain('mail.aol.com');
  });

  test('WHITELIST_DOMAINS includes accounts.google.com', () => {
    expect(WHITELIST_DOMAINS).toContain('accounts.google.com');
  });
});
