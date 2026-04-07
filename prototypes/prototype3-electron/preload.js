/**
 * preload.js
 * Electron preload script.
 *
 * Runs in the renderer process but with Node.js access.
 * Exposes a safe, minimal API to renderer/app.js via contextBridge.
 * Nothing here gives the renderer direct access to Node or Electron internals.
 */

'use strict';

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('gertrudeAPI', {

  // ── Config ──────────────────────────────────────────────────────────────────

  /** Load the persisted config object from main process. */
  getConfig: () => ipcRenderer.invoke('get-config'),

  /** Save an updated config object. */
  saveConfig: (config) => ipcRenderer.invoke('save-config', config),

  // ── Navigation ──────────────────────────────────────────────────────────────

  /** Tell main to open a URL in the WebContentsView. */
  openSite: (url) => ipcRenderer.send('open-site', url),

  /** Tell main to destroy the current WebContentsView (END button). */
  closeSite: () => ipcRenderer.send('close-site'),

  /** Tell main to minimise the window (show Windows desktop). */
  showDesktop: () => ipcRenderer.send('show-desktop'),

  // ── Photos ──────────────────────────────────────────────────────────────────

  /** Returns { gertrude: string|null, marty: string|null } photo file:// URLs. */
  getPhotoPaths: () => ipcRenderer.invoke('get-photo-paths'),

  // ── Events from main → renderer ─────────────────────────────────────────────

  /**
   * Register a listener for when main blocks a URL.
   * Callback receives (url: string).
   * Returns a cleanup function.
   */
  onUrlBlocked: (callback) => {
    const handler = (_event, url) => callback(url);
    ipcRenderer.on('url-blocked', handler);
    return () => ipcRenderer.removeListener('url-blocked', handler);
  },

  /**
   * Register a listener for when the embedded view navigates.
   * Callback receives (url: string).
   * Returns a cleanup function.
   */
  onViewNavigated: (callback) => {
    const handler = (_event, url) => callback(url);
    ipcRenderer.on('view-navigated', handler);
    return () => ipcRenderer.removeListener('view-navigated', handler);
  },

  // ── Dev helpers (disable in production) ─────────────────────────────────────
  openDevTools: () => ipcRenderer.send('open-devtools'),
});
