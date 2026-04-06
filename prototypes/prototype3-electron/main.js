/**
 * main.js
 * Electron main process for Gertrude Shell.
 *
 * Architecture:
 *   - BrowserWindow is the persistent "bevel" frame (header bar always visible).
 *   - The renderer (renderer/index.html) shows the main board OR sends an IPC
 *     message to open a site.
 *   - When a site is opened a WebContentsView is layered below the header bar.
 *   - URL security is enforced at the session level via webRequest.onBeforeRequest
 *     so nothing sneaks through regardless of redirect chains.
 */

'use strict';

const {
  app,
  BrowserWindow,
  WebContentsView,
  ipcMain,
  dialog,
  shell,
  nativeTheme,
  session,
} = require('electron');
const path = require('path');
const fs = require('fs');

const { isSafeUrl, loadConfig, saveConfig, DEFAULT_CONFIG, WHITELIST_DOMAINS } = require('./src/logic');

// ─── Paths ────────────────────────────────────────────────────────────────────

const USER_DATA_DIR = app.getPath('userData');
const CONFIG_PATH = path.join(USER_DATA_DIR, 'gertrude-config.json');

// Height of the persistent header bar (pixels).  Keep in sync with CSS.
const HEADER_HEIGHT = 80;

// ─── State ────────────────────────────────────────────────────────────────────

let mainWindow = null;
let activeView = null;   // WebContentsView currently shown, or null
let config = null;

// ─── Config helpers ───────────────────────────────────────────────────────────

function getConfig() {
  if (!config) {
    config = loadConfig(CONFIG_PATH);
  }
  return config;
}

function persistConfig(newConfig) {
  config = newConfig;
  saveConfig(CONFIG_PATH, newConfig);
}

// ─── URL Security (session-level) ─────────────────────────────────────────────

/**
 * Block any non-whitelisted URL before it is fetched, in the web view session.
 * This fires for all navigations AND sub-resource requests inside the view.
 *
 * We allow requests from the renderer (main board) itself unrestricted — those
 * are local file:// loads.
 */
function installUrlGuard() {
  // Use a dedicated partition so the main renderer is unaffected.
  const viewSession = session.fromPartition('persist:gview');

  viewSession.webRequest.onBeforeRequest({ urls: ['*://*/*'] }, (details, callback) => {
    const url = details.url;

    // Always allow local resources
    if (url.startsWith('file://') || url.startsWith('devtools://')) {
      callback({ cancel: false });
      return;
    }

    if (isSafeUrl(url)) {
      callback({ cancel: false });
    } else {
      // Cancel the request; the renderer will show a warning via IPC
      callback({ cancel: true });

      // Notify renderer about the blocked URL (fire-and-forget)
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('url-blocked', url);
      }
    }
  });
}

// ─── WebContentsView management ───────────────────────────────────────────────

function getViewBounds() {
  const [width, height] = mainWindow.getContentSize();
  return {
    x: 0,
    y: HEADER_HEIGHT,
    width,
    height: height - HEADER_HEIGHT,
  };
}

function openSiteView(url) {
  // Destroy any existing view first
  closeSiteView();

  const viewSession = session.fromPartition('persist:gview');

  activeView = new WebContentsView({
    webPreferences: {
      session: viewSession,
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      // Allow popups from Google/Facebook login flows
      allowPopups: true,
    },
  });

  mainWindow.contentView.addChildView(activeView);
  activeView.setBounds(getViewBounds());

  // Keep the view sized when the window is resized
  mainWindow.on('resize', adjustViewBounds);

  // Track navigation for context label updates
  activeView.webContents.on('did-navigate', (_event, navUrl) => {
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('view-navigated', navUrl);
    }
  });

  activeView.webContents.on('did-navigate-in-page', (_event, navUrl) => {
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('view-navigated', navUrl);
    }
  });

  // Security: intercept will-navigate (before navigation commits)
  activeView.webContents.on('will-navigate', (event, navUrl) => {
    if (!isSafeUrl(navUrl)) {
      event.preventDefault();
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('url-blocked', navUrl);
      }
    }
  });

  activeView.webContents.loadURL(url);
}

function adjustViewBounds() {
  if (activeView && !activeView.webContents.isDestroyed()) {
    activeView.setBounds(getViewBounds());
  }
}

function closeSiteView() {
  mainWindow.removeListener('resize', adjustViewBounds);

  if (activeView) {
    try {
      mainWindow.contentView.removeChildView(activeView);
      activeView.webContents.close();
    } catch (_) {
      // Already destroyed — ignore
    }
    activeView = null;
  }
}

// ─── Main Window ──────────────────────────────────────────────────────────────

function createMainWindow() {
  nativeTheme.themeSource = 'light';

  mainWindow = new BrowserWindow({
    width: 1024,
    height: 768,
    minWidth: 800,
    minHeight: 600,
    // For a real shell replacement you would use: kiosk: true, frame: false
    // We leave it windowed so it can be demoed easily on any machine.
    frame: true,
    title: 'Gertrude Shell',
    backgroundColor: '#FFF8F0',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: false, // preload needs path/fs via the bridge
    },
    icon: path.join(__dirname, 'photos', 'icon.png'), // optional; won't error if missing
  });

  mainWindow.maximize();
  mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// ─── IPC Handlers ─────────────────────────────────────────────────────────────

// Renderer asks for app config
ipcMain.handle('get-config', () => {
  return getConfig();
});

// Renderer saves updated config (first-run setup)
ipcMain.handle('save-config', (_event, newConfig) => {
  persistConfig(newConfig);
  return true;
});

// Renderer requests to open a site in the WebContentsView
ipcMain.on('open-site', (_event, url) => {
  if (!isSafeUrl(url)) {
    mainWindow.webContents.send('url-blocked', url);
    return;
  }
  openSiteView(url);
});

// Renderer requests to close the current site view (END button)
ipcMain.on('close-site', () => {
  closeSiteView();
});

// Renderer requests to minimise the window (Desktop button)
ipcMain.on('show-desktop', () => {
  if (mainWindow) mainWindow.minimize();
});

// Renderer asks for the paths to photos (so it can display them)
ipcMain.handle('get-photo-paths', () => {
  const photoDir = path.join(__dirname, 'photos');
  const resolve = (name) => {
    const full = path.join(photoDir, name);
    // Return file:// URL if exists, else null
    return fs.existsSync(full) ? `file://${full}` : null;
  };
  return {
    gertrude: resolve('gertrude.jpg') || resolve('gertrude.png'),
    marty: resolve('marty.jpg') || resolve('marty.png'),
  };
});

// Renderer asks to open DevTools (dev helper — remove in production)
ipcMain.on('open-devtools', () => {
  if (mainWindow) mainWindow.webContents.openDevTools({ mode: 'detach' });
});

// ─── App lifecycle ────────────────────────────────────────────────────────────

app.whenReady().then(() => {
  installUrlGuard();
  createMainWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createMainWindow();
  });
});

app.on('window-all-closed', () => {
  // On macOS it's conventional to keep the process alive; elsewhere quit.
  if (process.platform !== 'darwin') app.quit();
});
