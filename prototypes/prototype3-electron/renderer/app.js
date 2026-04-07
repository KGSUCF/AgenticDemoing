/**
 * renderer/app.js
 * Gertrude Shell — Renderer process logic.
 *
 * Runs inside the BrowserWindow renderer (index.html).
 * All Electron/Node access goes through window.gertrudeAPI (set up in preload.js).
 *
 * Responsibilities:
 *   1. Load config from main process; show first-run setup if needed.
 *   2. Load & display Gertrude/Marty photos.
 *   3. Drive the live clock and greeting in the header.
 *   4. Handle app button clicks (open site via IPC, or Desktop/minimize).
 *   5. Handle END button (close site view via IPC, return to main board UI).
 *   6. Show "blocked URL" warning dialog when main process blocks a navigation.
 *   7. Update context label when the embedded site navigates.
 */

'use strict';

// ── App definitions (must match main.js / logic.js) ─────────────────────────

const APPS = [
  { id: 'facebook', label: 'Facebook',          url: 'https://www.facebook.com' },
  { id: 'milo',     label: 'Milo (Google Photos)', url: 'https://photos.google.com' },
  { id: 'aolnews',  label: 'AOL News',           url: 'https://www.aol.com'      },
  { id: 'aolmail',  label: 'AOL Mail',           url: 'https://mail.aol.com'     },
  { id: 'desktop',  label: 'Desktop',            action: 'desktop'               },
];

// ── DOM references ────────────────────────────────────────────────────────────

const headerContext  = document.getElementById('header-context');
const endBtn         = document.getElementById('end-btn');
const mainBoard      = document.getElementById('main-board');
const clockEl        = document.getElementById('clock');
const photoGertrude  = document.getElementById('photo-gertrude');
const photoMarty     = document.getElementById('photo-marty');

const blockedOverlay = document.getElementById('blocked-overlay');
const blockedOkBtn   = document.getElementById('blocked-ok-btn');

const setupOverlay   = document.getElementById('setup-overlay');
const setupSaveBtn   = document.getElementById('setup-save-btn');

// ── State ─────────────────────────────────────────────────────────────────────

let currentApp = null;   // id of the currently open app, or null
let clockTimer = null;

// ── Greeting helper (mirrors logic.js — renderer can't require() it) ─────────

/**
 * Returns "Good Morning/Afternoon/Evening, Gertrude!" based on hour.
 * @param {number} hour 0-23
 */
function getGreeting(hour) {
  if (hour >= 5 && hour < 12)  return 'Good Morning, Gertrude!';
  if (hour >= 12 && hour < 18) return 'Good Afternoon, Gertrude!';
  return 'Good Evening, Gertrude!';
}

// ── Clock ─────────────────────────────────────────────────────────────────────

function formatTime(date) {
  let h = date.getHours();
  const m = String(date.getMinutes()).padStart(2, '0');
  const ampm = h >= 12 ? 'PM' : 'AM';
  h = h % 12 || 12;
  return `${h}:${m} ${ampm}`;
}

function tickClock() {
  const now = new Date();
  clockEl.textContent = formatTime(now);

  // Update greeting in header when on main board
  if (!currentApp) {
    headerContext.textContent = getGreeting(now.getHours());
  }
}

function startClock() {
  tickClock();
  // Align to the next full minute
  const msToNextMinute = (60 - new Date().getSeconds()) * 1000;
  setTimeout(() => {
    tickClock();
    clockTimer = setInterval(tickClock, 60_000);
  }, msToNextMinute);
}

// ── Photos ────────────────────────────────────────────────────────────────────

async function loadPhotos() {
  try {
    const paths = await window.gertrudeAPI.getPhotoPaths();

    if (paths.gertrude) {
      const img = document.createElement('img');
      img.src = paths.gertrude;
      img.alt = 'Gertrude';
      img.width = 160;
      img.height = 160;
      photoGertrude.replaceWith(img);
      img.id = 'photo-gertrude';
    }

    if (paths.marty) {
      const img = document.createElement('img');
      img.src = paths.marty;
      img.alt = 'Marty';
      img.width = 160;
      img.height = 160;
      photoMarty.replaceWith(img);
      img.id = 'photo-marty';
    }
  } catch (err) {
    console.warn('Could not load photos:', err);
    // Fallback emoji placeholders already in the DOM — nothing to do.
  }
}

// ── Main board / site view toggle ────────────────────────────────────────────

function showMainBoard() {
  currentApp = null;
  mainBoard.classList.remove('hidden');
  endBtn.classList.add('hidden');

  // Restore greeting in header
  const now = new Date();
  headerContext.textContent = getGreeting(now.getHours());
}

function showSiteView(appId, label) {
  currentApp = appId;
  mainBoard.classList.add('hidden');
  endBtn.classList.remove('hidden');
  headerContext.textContent = label;
}

// ── App button click handler ──────────────────────────────────────────────────

function handleAppClick(appId) {
  const app = APPS.find(a => a.id === appId);
  if (!app) return;

  if (app.action === 'desktop') {
    window.gertrudeAPI.showDesktop();
    return;
  }

  // Switch UI to site view mode immediately for responsiveness
  showSiteView(app.id, app.label);

  // Ask main process to create the WebContentsView
  window.gertrudeAPI.openSite(app.url);
}

// ── END button ────────────────────────────────────────────────────────────────

endBtn.addEventListener('click', () => {
  window.gertrudeAPI.closeSite();
  showMainBoard();
});

// ── App buttons ───────────────────────────────────────────────────────────────

document.getElementById('apps-grid').addEventListener('click', (e) => {
  const btn = e.target.closest('[data-app]');
  if (!btn) return;
  handleAppClick(btn.dataset.app);
});

// ── Blocked URL dialog ────────────────────────────────────────────────────────

let blockedCleanup = null;

function showBlockedDialog(url) {
  const msg = document.getElementById('blocked-msg');
  // Show a friendly message without exposing the raw URL to Gertrude
  msg.textContent = 'That website is not available here. Please ask for help if you need it.';
  blockedOverlay.classList.remove('hidden');
  blockedOkBtn.focus();
  console.warn('[Security] Blocked URL:', url);
}

blockedOkBtn.addEventListener('click', () => {
  blockedOverlay.classList.add('hidden');
});

// Close on backdrop click
blockedOverlay.addEventListener('click', (e) => {
  if (e.target === blockedOverlay) {
    blockedOverlay.classList.add('hidden');
  }
});

// Keyboard dismiss
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && !blockedOverlay.classList.contains('hidden')) {
    blockedOverlay.classList.add('hidden');
  }
});

// ── Navigation context updates ───────────────────────────────────────────────

/**
 * Maps a URL to a friendly app name for the header context label.
 * Mirrors getAppDisplayName in logic.js — inline here so renderer needs no require().
 */
function getDisplayNameFromUrl(url) {
  try {
    const { hostname } = new URL(url);
    const h = hostname.toLowerCase();
    if (h === 'www.facebook.com' || h === 'facebook.com') return 'Facebook';
    if (h === 'photos.google.com')                         return 'Milo (Google Photos)';
    if (h === 'mail.aol.com')                              return 'AOL Mail';
    if (h === 'www.aol.com' || h === 'aol.com')            return 'AOL News';
    if (h === 'accounts.google.com')                       return 'Google Sign-In';
    if (h.endsWith('google.com'))                          return 'Google';
    return h;
  } catch (_) {
    return '';
  }
}

// ── First-run setup modal ─────────────────────────────────────────────────────

function showSetupModal(config) {
  // Pre-fill any saved credentials
  document.getElementById('fb-user').value  = config?.credentials?.facebook?.username  || '';
  document.getElementById('fb-pass').value  = config?.credentials?.facebook?.password  || '';
  document.getElementById('aol-user').value = config?.credentials?.aolmail?.username || '';
  document.getElementById('aol-pass').value = config?.credentials?.aolmail?.password || '';
  setupOverlay.classList.remove('hidden');
  document.getElementById('fb-user').focus();
}

setupSaveBtn.addEventListener('click', async () => {
  const config = {
    setupComplete: true,
    firstRun: false,
    userName: 'Gertrude',
    credentials: {
      facebook: {
        username: document.getElementById('fb-user').value.trim(),
        password: document.getElementById('fb-pass').value,
      },
      aolmail: {
        username: document.getElementById('aol-user').value.trim(),
        password: document.getElementById('aol-pass').value,
      },
    },
  };

  try {
    await window.gertrudeAPI.saveConfig(config);
  } catch (err) {
    console.error('Failed to save config:', err);
  }

  setupOverlay.classList.add('hidden');
});

// Allow Enter key to submit setup form
document.getElementById('setup-dialog').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    setupSaveBtn.click();
  }
});

// ── IPC event listeners ───────────────────────────────────────────────────────

function registerIpcListeners() {
  // Blocked URL from main process (session-level block)
  window.gertrudeAPI.onUrlBlocked((url) => {
    showBlockedDialog(url);
  });

  // View navigated — update header context label
  window.gertrudeAPI.onViewNavigated((url) => {
    if (currentApp) {
      const name = getDisplayNameFromUrl(url);
      if (name) {
        headerContext.textContent = name;
      }
    }
  });
}

// ── Initialisation ────────────────────────────────────────────────────────────

async function init() {
  // Start clock immediately
  startClock();

  // Load photos asynchronously (non-blocking)
  loadPhotos();

  // Register IPC event listeners
  registerIpcListeners();

  // Load config and decide whether to show first-run setup
  try {
    const config = await window.gertrudeAPI.getConfig();
    if (config && !config.setupComplete) {
      showSetupModal(config);
    }
  } catch (err) {
    console.warn('Could not load config:', err);
  }

  // Initial header state
  showMainBoard();
}

// Start when DOM is ready (script loaded at end of body so it's already ready)
init().catch(console.error);
