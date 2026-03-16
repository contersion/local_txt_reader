import { authTokenStorage } from "../utils/token";
import type { ApiErrorResponse } from "../types/api";
import { getActiveApiBaseUrl } from "../utils/backend";

function getFallbackOrigin() {
  return typeof window === "undefined" ? "http://127.0.0.1" : window.location.origin;
}

function trimTrailingSlashes(value: string) {
  return value.replace(/\/+$/, "");
}

function buildBaseAwareUrl(baseUrl: string, path: string) {
  if (!baseUrl) {
    return new URL(path, getFallbackOrigin()).toString();
  }

  if (/^https?:\/\//i.test(baseUrl)) {
    return `${trimTrailingSlashes(baseUrl)}${path}`;
  }

  const resolvedBaseUrl = new URL(baseUrl, getFallbackOrigin());
  const normalizedBasePath = trimTrailingSlashes(resolvedBaseUrl.pathname);
  resolvedBaseUrl.pathname = `${normalizedBasePath}${path}`;
  resolvedBaseUrl.search = "";
  resolvedBaseUrl.hash = "";
  return resolvedBaseUrl.toString();
}

export function getApiBaseUrl() {
  return getActiveApiBaseUrl();
}

export function resolveApiAssetUrl(path: string | null | undefined) {
  if (!path) {
    return null;
  }

  if (/^https?:\/\//i.test(path)) {
    return path;
  }

  const apiBaseUrl = getApiBaseUrl();

  if (path.startsWith("/")) {
    return apiBaseUrl ? buildBaseAwareUrl(apiBaseUrl, path) : path;
  }

  return apiBaseUrl ? buildBaseAwareUrl(apiBaseUrl, `/${path}`) : `/${path}`;
}

type QueryValue = string | number | boolean | null | undefined;
type RequestBody = BodyInit | FormData | URLSearchParams | object | null | undefined;

export class ApiError extends Error {
  status: number;
  code?: string;
  details?: unknown;

  constructor(message: string, status: number, code?: string, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  query?: Record<string, QueryValue>;
  body?: RequestBody;
  headers?: HeadersInit;
  auth?: boolean;
  signal?: AbortSignal;
}

function isApiErrorResponse(payload: unknown): payload is ApiErrorResponse {
  return typeof payload === "object" && payload !== null && ("error" in payload || "detail" in payload);
}

function isRawBody(body: RequestBody): body is BodyInit {
  return (
    typeof body === "string" ||
    body instanceof Blob ||
    body instanceof FormData ||
    body instanceof URLSearchParams ||
    body instanceof ArrayBuffer
  );
}

function formatErrorDetail(detail: ApiErrorResponse["detail"]) {
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  if (Array.isArray(detail) && detail.length > 0) {
    return detail
      .map((item) => item.msg || "请求参数不合法")
      .join("；");
  }

  return "请求失败，请稍后再试";
}

export function buildApiUrl(path: string, query?: Record<string, QueryValue>) {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const url = new URL(
    buildBaseAwareUrl(getApiBaseUrl(), normalizedPath),
  );

  Object.entries(query || {}).forEach(([key, value]) => {
    if (value === null || value === undefined || value === "") {
      return;
    }

    url.searchParams.set(key, String(value));
  });

  return url.toString();
}

async function request<T>(path: string, options: RequestOptions = {}) {
  const {
    method = "GET",
    query,
    body,
    headers,
    auth = true,
    signal,
  } = options;

  const requestHeaders = new Headers(headers);
  const token = authTokenStorage.get();

  if (auth && token) {
    requestHeaders.set("Authorization", `Bearer ${token}`);
  }

  let payload: BodyInit | undefined;

  if (isRawBody(body)) {
    payload = body;
  } else if (body !== undefined && body !== null) {
    requestHeaders.set("Content-Type", "application/json");
    payload = JSON.stringify(body);
  }

  let response: Response;

  try {
    response = await fetch(buildApiUrl(path, query), {
      method,
      headers: requestHeaders,
      body: payload,
      signal,
    });
  } catch (error) {
    const message = error instanceof DOMException && error.name === "AbortError"
      ? "请求已取消"
      : "无法连接到后端服务，请确认后端已启动";

    throw new ApiError(message, 0, "NETWORK_ERROR", error);
  }

  const contentType = response.headers.get("content-type") || "";
  const data = response.status === 204
    ? undefined
    : contentType.includes("application/json")
      ? await response.json()
      : await response.text();

  if (!response.ok) {
    if (isApiErrorResponse(data)) {
      const message = data.error?.message || formatErrorDetail(data.detail);
      throw new ApiError(message, response.status, data.error?.code, data.error?.details ?? data.detail);
    }

    if (typeof data === "string" && data.trim()) {
      throw new ApiError(data, response.status, undefined, data);
    }

    throw new ApiError(response.statusText || "请求失败", response.status, undefined, data);
  }

  return data as T;
}

export function getErrorMessage(error: unknown) {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "请求失败，请稍后再试";
}

export const apiClient = {
  get<T>(path: string, options?: Omit<RequestOptions, "method" | "body">) {
    return request<T>(path, { ...options, method: "GET" });
  },
  post<T>(path: string, body?: RequestOptions["body"], options?: Omit<RequestOptions, "method" | "body">) {
    return request<T>(path, { ...options, method: "POST", body });
  },
  put<T>(path: string, body?: RequestOptions["body"], options?: Omit<RequestOptions, "method" | "body">) {
    return request<T>(path, { ...options, method: "PUT", body });
  },
  patch<T>(path: string, body?: RequestOptions["body"], options?: Omit<RequestOptions, "method" | "body">) {
    return request<T>(path, { ...options, method: "PATCH", body });
  },
  delete<T>(path: string, options?: Omit<RequestOptions, "method" | "body">) {
    return request<T>(path, { ...options, method: "DELETE" });
  },
};
