import { defineStore } from "pinia";

export type AppThemeMode = "light" | "dark";

const APP_THEME_STORAGE_KEY = "txt-reader.app-theme";
const LEGACY_READER_PREFERENCES_KEY = "txt-reader.preferences";
const APP_THEME_CLASS_PREFIX = "app-theme--";

function normalizeTheme(value: unknown): AppThemeMode {
  return value === "dark" ? "dark" : "light";
}

function readThemeFromStorage(): {
  theme: AppThemeMode;
  hasStoredPreference: boolean;
} {
  if (typeof window === "undefined") {
    return {
      theme: "light",
      hasStoredPreference: false,
    };
  }

  try {
    const storedTheme = window.localStorage.getItem(APP_THEME_STORAGE_KEY);
    if (storedTheme) {
      return {
        theme: normalizeTheme(storedTheme),
        hasStoredPreference: true,
      };
    }

    const legacyReaderPreferences = window.localStorage.getItem(LEGACY_READER_PREFERENCES_KEY);
    if (!legacyReaderPreferences) {
      return {
        theme: "light",
        hasStoredPreference: false,
      };
    }

    const parsed = JSON.parse(legacyReaderPreferences) as {
      theme?: AppThemeMode;
    };

    return {
      theme: normalizeTheme(parsed.theme),
      hasStoredPreference: false,
    };
  } catch {
    return {
      theme: "light",
      hasStoredPreference: false,
    };
  }
}

function persistTheme(theme: AppThemeMode) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(APP_THEME_STORAGE_KEY, theme);
}

function applyThemeToDocument(theme: AppThemeMode) {
  if (typeof document === "undefined") {
    return;
  }

  const nextThemeClass = `${APP_THEME_CLASS_PREFIX}${theme}`;
  document.body.classList.remove(`${APP_THEME_CLASS_PREFIX}light`, `${APP_THEME_CLASS_PREFIX}dark`);
  document.body.classList.add(nextThemeClass);
  document.documentElement.style.colorScheme = theme;
}

interface AppThemeState {
  theme: AppThemeMode;
  initialized: boolean;
  hasStoredPreference: boolean;
}

export const useAppThemeStore = defineStore("app-theme", {
  state: (): AppThemeState => ({
    theme: "light",
    initialized: false,
    hasStoredPreference: false,
  }),
  actions: {
    initialize() {
      const { theme, hasStoredPreference } = readThemeFromStorage();
      this.theme = theme;
      this.initialized = true;
      this.hasStoredPreference = hasStoredPreference;
      applyThemeToDocument(theme);
    },
    setTheme(theme: AppThemeMode, markAsStoredPreference = true) {
      const normalizedTheme = normalizeTheme(theme);
      this.theme = normalizedTheme;

      if (markAsStoredPreference) {
        this.hasStoredPreference = true;
        persistTheme(normalizedTheme);
      }

      applyThemeToDocument(normalizedTheme);
    },
    toggleTheme() {
      this.setTheme(this.theme === "dark" ? "light" : "dark");
    },
  },
});
