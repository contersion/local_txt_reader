import { ApiError, apiClient } from "./client";
import type {
  LegadoImportIssue,
  LegadoImportResult,
  OnlineSourceSummary,
} from "../types/api";

function isLegadoImportIssue(value: unknown): value is LegadoImportIssue {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const issue = value as Partial<LegadoImportIssue>;
  return typeof issue.code === "string" && typeof issue.message === "string";
}

function isLegadoImportResult(value: unknown): value is LegadoImportResult {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const result = value as Partial<LegadoImportResult>;
  return (
    typeof result.is_valid === "boolean" &&
    Array.isArray(result.errors) &&
    Array.isArray(result.warnings) &&
    result.errors.every(isLegadoImportIssue) &&
    result.warnings.every(isLegadoImportIssue)
  );
}

export function getLegadoImportResultFromError(error: unknown) {
  if (!(error instanceof ApiError)) {
    return null;
  }

  return isLegadoImportResult(error.details) ? error.details : null;
}

export function getLegadoIssueCode(issue: LegadoImportIssue) {
  return issue.error_code || issue.code || "UNKNOWN";
}

export function collectLegadoIssueCodes(issues: LegadoImportIssue[]) {
  return Array.from(new Set(issues.map(getLegadoIssueCode).filter(Boolean)));
}

export const onlineSourcesApi = {
  list() {
    return apiClient.get<OnlineSourceSummary[]>("/api/online-sources");
  },
  importLegado(source: Record<string, unknown>) {
    return apiClient.post<LegadoImportResult>("/api/online-sources/import", { source });
  },
};
