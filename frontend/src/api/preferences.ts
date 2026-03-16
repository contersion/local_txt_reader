import { apiClient } from "./client";
import type { ApiUserPreferencesPatchRequest, ApiUserPreferencesResponse } from "../types/api";


export const preferencesApi = {
  get() {
    return apiClient.get<ApiUserPreferencesResponse>("/api/preferences");
  },
  patch(payload: ApiUserPreferencesPatchRequest) {
    return apiClient.patch<ApiUserPreferencesResponse>("/api/preferences", payload);
  },
};
