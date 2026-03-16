export type BackendMode = "local" | "remote";

export interface BackendConfig {
  mode: BackendMode;
  remoteBaseUrl: string | null;
}

export interface BackendNotice {
  type: "success" | "error" | "info";
  text: string;
}

const BACKEND_CONFIG_STORAGE_KEY = "txt-reader/backend-config";
const BACKEND_NOTICE_STORAGE_KEY = "txt-reader/backend-notice";
const LOOPBACK_HOSTNAMES = new Set(["localhost", "127.0.0.1", "[::1]"]);

function isLoopbackHostname(hostname: string) {
  return LOOPBACK_HOSTNAMES.has(hostname.trim().toLowerCase());
}

function trimEnvValue(value: unknown) {
  return typeof value === "string" ? value.trim() : "";
}

function getFallbackOrigin() {
  return typeof window === "undefined" ? "http://127.0.0.1" : window.location.origin;
}

function canUseLoopbackBaseUrl() {
  if (typeof window === "undefined") {
    return true;
  }

  const protocol = window.location.protocol.toLowerCase();
  if (protocol === "file:" || protocol === "app:") {
    return true;
  }

  return isLoopbackHostname(window.location.hostname);
}

function trimTrailingSlashes(value: string) {
  return value.replace(/\/+$/, "");
}

function normalizeStoredBaseUrl(input: string) {
  const trimmed = input.trim();
  if (!trimmed) {
    return "";
  }

  try {
    const parsedUrl = new URL(trimmed, getFallbackOrigin());

    if (isLoopbackHostname(parsedUrl.hostname) && !canUseLoopbackBaseUrl()) {
      return "";
    }
  } catch {
    // Keep the original value when parsing fails so existing deployments keep working.
  }

  return trimTrailingSlashes(trimmed);
}

function normalizeAbsoluteBaseUrl(url: URL) {
  const normalizedPath = trimTrailingSlashes(url.pathname);
  return `${url.origin}${normalizedPath}`;
}

export function getRemoteBaseUrlValidationMessage(input: string | null | undefined) {
  const trimmed = typeof input === "string" ? input.trim() : "";
  if (!trimmed) {
    return "请输入远程后端地址。";
  }

  let parsedUrl: URL;

  try {
    parsedUrl = new URL(trimmed);
  } catch {
    return "请输入完整的 http(s) 地址，例如 https://example.com。";
  }

  if (!/^https?:$/i.test(parsedUrl.protocol)) {
    return "远程后端地址只支持 http 或 https。";
  }

  if (parsedUrl.search || parsedUrl.hash) {
    return "远程后端地址不要包含查询参数或锚点。";
  }

  if (trimTrailingSlashes(parsedUrl.pathname).toLowerCase().endsWith("/api")) {
    return "请填写后端根地址，不要带 /api。";
  }

  return null;
}

export function normalizeRemoteBaseUrl(input: string | null | undefined) {
  const validationMessage = getRemoteBaseUrlValidationMessage(input);
  if (validationMessage) {
    return null;
  }

  return normalizeAbsoluteBaseUrl(new URL(String(input).trim()));
}

export function getDefaultLocalApiBaseUrl() {
  const localEnvBaseUrl = trimEnvValue(import.meta.env.VITE_LOCAL_API_BASE_URL);
  if (localEnvBaseUrl) {
    return normalizeStoredBaseUrl(localEnvBaseUrl);
  }

  const compatibleEnvBaseUrl = trimEnvValue(import.meta.env.VITE_API_BASE_URL);
  if (compatibleEnvBaseUrl) {
    return normalizeStoredBaseUrl(compatibleEnvBaseUrl);
  }

  return "";
}

export function getDefaultBackendConfig(): BackendConfig {
  return {
    mode: "local",
    remoteBaseUrl: null,
  };
}

export function normalizeBackendConfig(input?: Partial<BackendConfig> | null): BackendConfig {
  const mode: BackendMode = input?.mode === "remote" ? "remote" : "local";
  const remoteBaseUrl = normalizeRemoteBaseUrl(input?.remoteBaseUrl);

  if (mode === "remote" && !remoteBaseUrl) {
    return getDefaultBackendConfig();
  }

  return {
    mode,
    remoteBaseUrl,
  };
}

export function loadBackendConfig() {
  if (typeof window === "undefined") {
    return getDefaultBackendConfig();
  }

  try {
    const rawValue = window.localStorage.getItem(BACKEND_CONFIG_STORAGE_KEY);
    if (!rawValue) {
      return getDefaultBackendConfig();
    }

    const parsedValue = JSON.parse(rawValue) as Partial<BackendConfig>;
    return normalizeBackendConfig(parsedValue);
  } catch {
    return getDefaultBackendConfig();
  }
}

export function saveBackendConfig(input: BackendConfig) {
  const normalizedConfig = normalizeBackendConfig(input);

  if (typeof window !== "undefined") {
    window.localStorage.setItem(
      BACKEND_CONFIG_STORAGE_KEY,
      JSON.stringify(normalizedConfig),
    );
  }

  return normalizedConfig;
}

export function getActiveApiBaseUrl(config = loadBackendConfig()) {
  if (config.mode === "remote" && config.remoteBaseUrl) {
    return config.remoteBaseUrl;
  }

  return getDefaultLocalApiBaseUrl();
}

export function getBackendIdFromBaseUrl(baseUrl: string) {
  const trimmed = baseUrl.trim();

  if (!trimmed) {
    if (typeof window !== "undefined" && window.location.origin) {
      return `origin:${window.location.origin.toLowerCase()}`;
    }

    return "local";
  }

  try {
    const parsedUrl = new URL(trimmed, getFallbackOrigin());
    const normalizedOrigin = `${parsedUrl.protocol}//${parsedUrl.host}`.toLowerCase();
    const normalizedPath = trimTrailingSlashes(parsedUrl.pathname);

    return normalizedPath && normalizedPath !== "/"
      ? `${normalizedOrigin}${normalizedPath}`
      : normalizedOrigin;
  } catch {
    return trimmed.toLowerCase();
  }
}

export function getBackendIdForConfig(config = loadBackendConfig()) {
  return getBackendIdFromBaseUrl(getActiveApiBaseUrl(config));
}

export function getActiveBackendId() {
  return getBackendIdForConfig(loadBackendConfig());
}

export function getBackendDisplaySummary(config = loadBackendConfig()) {
  if (config.mode === "remote" && config.remoteBaseUrl) {
    return `远程后端 - ${config.remoteBaseUrl}`;
  }

  const localApiBaseUrl = getDefaultLocalApiBaseUrl();
  return localApiBaseUrl
    ? `本地后端 - ${localApiBaseUrl}`
    : "本地后端 - 同源 /api";
}

export function isSameBackendConfig(left: BackendConfig, right: BackendConfig) {
  const normalizedLeft = normalizeBackendConfig(left);
  const normalizedRight = normalizeBackendConfig(right);

  return normalizedLeft.mode === normalizedRight.mode
    && normalizedLeft.remoteBaseUrl === normalizedRight.remoteBaseUrl;
}

export function storeBackendNotice(notice: BackendNotice) {
  if (typeof window === "undefined") {
    return;
  }

  window.sessionStorage.setItem(
    BACKEND_NOTICE_STORAGE_KEY,
    JSON.stringify(notice),
  );
}

export function consumeBackendNotice() {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const rawValue = window.sessionStorage.getItem(BACKEND_NOTICE_STORAGE_KEY);
    if (!rawValue) {
      return null;
    }

    window.sessionStorage.removeItem(BACKEND_NOTICE_STORAGE_KEY);
    return JSON.parse(rawValue) as BackendNotice;
  } catch {
    window.sessionStorage.removeItem(BACKEND_NOTICE_STORAGE_KEY);
    return null;
  }
}
