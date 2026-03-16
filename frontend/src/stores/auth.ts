import { defineStore } from "pinia";

import { authApi } from "../api/auth";
import { ApiError, getErrorMessage } from "../api/client";
import type { LoginPayload, User } from "../types/api";
import { getActiveBackendId } from "../utils/backend";
import { authTokenStorage } from "../utils/token";

interface AuthState {
  backendId: string;
  token: string | null;
  user: User | null;
  initialized: boolean;
  restorePending: boolean;
  loginPending: boolean;
  errorMessage: string | null;
  bootstrapPromise: Promise<void> | null;
}

function createAuthState(): AuthState {
  const backendId = getActiveBackendId();

  return {
    backendId,
    token: authTokenStorage.get(backendId),
    user: null,
    initialized: false,
    restorePending: false,
    loginPending: false,
    errorMessage: null,
    bootstrapPromise: null,
  };
}

export const useAuthStore = defineStore("auth", {
  state: (): AuthState => createAuthState(),
  getters: {
    hasToken: (state) => Boolean(state.token),
    isAuthenticated: (state) => Boolean(state.token && state.user),
    isRestoringSession: (state) => state.restorePending,
  },
  actions: {
    syncBackendContext(options: { useStoredToken?: boolean } = {}) {
      const activeBackendId = getActiveBackendId();

      if (this.backendId === activeBackendId) {
        return false;
      }

      this.backendId = activeBackendId;
      this.token = options.useStoredToken === false ? null : authTokenStorage.get(activeBackendId);
      this.user = null;
      this.initialized = false;
      this.restorePending = false;
      this.loginPending = false;
      this.errorMessage = null;
      this.bootstrapPromise = null;

      return true;
    },
    async ensureReady() {
      this.syncBackendContext();

      if (this.initialized) {
        return;
      }

      if (!this.bootstrapPromise) {
        this.bootstrapPromise = this.bootstrap().finally(() => {
          this.bootstrapPromise = null;
        });
      }

      await this.bootstrapPromise;
    },
    async bootstrap() {
      this.syncBackendContext();

      if (!this.token) {
        this.initialized = true;
        this.restorePending = false;
        return;
      }

      this.restorePending = true;

      try {
        this.user = await authApi.getCurrentUser();
        this.errorMessage = null;
      } catch (error) {
        const message = error instanceof ApiError && error.status === 401
          ? "Your session has expired. Please log in again."
          : getErrorMessage(error);

        this.clearAuth();
        this.errorMessage = message;
      } finally {
        this.restorePending = false;
        this.initialized = true;
      }
    },
    async login(payload: LoginPayload) {
      this.syncBackendContext({ useStoredToken: false });
      this.loginPending = true;
      this.errorMessage = null;

      try {
        const tokenResponse = await authApi.login(payload);
        this.setToken(tokenResponse.access_token);
        this.user = await authApi.getCurrentUser();
        this.initialized = true;
      } catch (error) {
        this.clearAuth();
        this.errorMessage = getErrorMessage(error);
        throw error;
      } finally {
        this.loginPending = false;
      }
    },
    logout() {
      this.clearAuth();
      this.initialized = true;
      this.restorePending = false;
      this.loginPending = false;
      this.errorMessage = null;
    },
    handleBackendSwitch(nextBackendId = getActiveBackendId()) {
      this.backendId = nextBackendId;
      this.token = null;
      this.user = null;
      this.initialized = false;
      this.restorePending = false;
      this.loginPending = false;
      this.errorMessage = null;
      this.bootstrapPromise = null;
    },
    setError(message: string | null) {
      this.errorMessage = message;
    },
    setToken(token: string) {
      const activeBackendId = getActiveBackendId();

      this.backendId = activeBackendId;
      this.token = token;
      authTokenStorage.set(token, activeBackendId);
    },
    clearAuth(options: { clearStorage?: boolean } = {}) {
      const backendId = this.backendId || getActiveBackendId();

      this.token = null;
      this.user = null;

      if (options.clearStorage !== false) {
        authTokenStorage.clear(backendId);
      }
    },
  },
});
