import { getActiveBackendId, loadBackendConfig } from "./backend";

const LEGACY_TOKEN_STORAGE_KEY = "txt-reader/token";

function buildScopedTokenStorageKey(backendId: string) {
  return `${LEGACY_TOKEN_STORAGE_KEY}/${encodeURIComponent(backendId)}`;
}

function readLegacyToken(backendId: string) {
  if (typeof window === "undefined") {
    return null;
  }

  const activeConfig = loadBackendConfig();
  if (activeConfig.mode !== "local" || backendId !== getActiveBackendId()) {
    return null;
  }

  return window.localStorage.getItem(LEGACY_TOKEN_STORAGE_KEY);
}

export const authTokenStorage = {
  get(backendId = getActiveBackendId()) {
    const scopedToken = window.localStorage.getItem(buildScopedTokenStorageKey(backendId));
    return scopedToken || readLegacyToken(backendId);
  },
  set(token: string, backendId = getActiveBackendId()) {
    window.localStorage.setItem(buildScopedTokenStorageKey(backendId), token);
    window.localStorage.removeItem(LEGACY_TOKEN_STORAGE_KEY);
  },
  clear(backendId = getActiveBackendId()) {
    window.localStorage.removeItem(buildScopedTokenStorageKey(backendId));
    window.localStorage.removeItem(LEGACY_TOKEN_STORAGE_KEY);
  },
  clearLegacy() {
    window.localStorage.removeItem(LEGACY_TOKEN_STORAGE_KEY);
  },
};
