import { createDiscreteApi } from "naive-ui";

import { ApiError, getErrorMessage } from "../api/client";

const { message } = createDiscreteApi(["message"]);

let handlersInstalled = false;
let lastShownMessage = "";
let lastShownAt = 0;
const RESIZE_OBSERVER_BROWSER_NOISE_MESSAGES = new Set([
  "ResizeObserver loop completed with undelivered notifications.",
  "ResizeObserver loop limit exceeded",
]);

function shouldSuppressDuplicate(messageText: string) {
  const now = Date.now();
  const isDuplicate = messageText === lastShownMessage && now - lastShownAt < 1800;

  lastShownMessage = messageText;
  lastShownAt = now;

  return isDuplicate;
}

export function normalizeErrorMessage(error: unknown, fallback = "出现了未处理的异常，请稍后重试") {
  if (error instanceof ApiError) {
    return getErrorMessage(error);
  }

  if (error instanceof Error && error.message) {
    return error.message;
  }

  if (typeof error === "string" && error.trim()) {
    return error.trim();
  }

  return fallback;
}

export function notifyGlobalError(error: unknown, fallback?: string) {
  const messageText = normalizeErrorMessage(error, fallback);

  if (shouldSuppressDuplicate(messageText)) {
    return;
  }

  message.error(messageText, {
    duration: 4000,
  });
}

function isIgnoredWindowErrorEvent(event: ErrorEvent) {
  const messageText = typeof event.message === "string" ? event.message.trim() : "";
  if (!RESIZE_OBSERVER_BROWSER_NOISE_MESSAGES.has(messageText)) {
    return false;
  }

  // Keep real runtime exceptions visible if the browser attached an actual error object.
  if (event.error != null) {
    return false;
  }

  const filename = typeof event.filename === "string" ? event.filename.trim() : "";
  const hasSourceLocation = filename.length > 0 || event.lineno > 0 || event.colno > 0;

  return !hasSourceLocation;
}

export function installGlobalErrorHandling() {
  if (handlersInstalled || typeof window === "undefined") {
    return;
  }

  handlersInstalled = true;

  window.addEventListener("error", (event) => {
    if (isIgnoredWindowErrorEvent(event)) {
      return;
    }

    notifyGlobalError(event.error ?? event.message, "页面出现异常，请刷新后重试");
  });

  window.addEventListener("unhandledrejection", (event) => {
    notifyGlobalError(event.reason, "请求处理失败，请稍后重试");
  });
}
