import { defineStore } from "pinia";

import { preferencesApi } from "../api/preferences";
import { getErrorMessage } from "../api/client";
import type {
  ApiBookshelfPreferences,
  ApiBookshelfPreferencesPatch,
  ApiReaderPreferences,
  ApiReaderPreferencesPatch,
  ApiUserPreferencesPatchRequest,
  ApiUserPreferencesResponse,
  BookSortKey,
} from "../types/api";


const LEGACY_READER_PREFERENCES_KEY = "txt-reader.preferences";
const SAVE_DEBOUNCE_MS = 450;

export interface BookshelfPreferencesState {
  sort: BookSortKey;
  search: string;
  groupId: number | null;
  page: number;
  pageSize: number | null;
}

export interface ReaderPreferencesState {
  fontSize: number;
  lineHeight: number;
  letterSpacing: number;
  paragraphSpacing: number;
  contentWidth: number;
  theme: "light" | "dark";
}

interface PreferencesState {
  version: number;
  bookshelf: BookshelfPreferencesState;
  reader: ReaderPreferencesState;
  initialized: boolean;
  loading: boolean;
  saving: boolean;
  hasSavedPreferences: boolean;
  errorMessage: string | null;
  saveErrorMessage: string | null;
  bootstrapPromise: Promise<void> | null;
}

export const DEFAULT_BOOKSHELF_PREFERENCES: BookshelfPreferencesState = {
  sort: "created_at",
  search: "",
  groupId: null,
  page: 1,
  pageSize: null,
};

export const DEFAULT_READER_PREFERENCES: ReaderPreferencesState = {
  fontSize: 19,
  lineHeight: 1.95,
  letterSpacing: 0,
  paragraphSpacing: 1,
  contentWidth: 72,
  theme: "light",
};

let pendingPatch: ApiUserPreferencesPatchRequest = {};
let saveTimer: ReturnType<typeof setTimeout> | null = null;
let savePromise: Promise<void> | null = null;

function createDefaultBookshelfPreferences(): BookshelfPreferencesState {
  return { ...DEFAULT_BOOKSHELF_PREFERENCES };
}

function createDefaultReaderPreferences(): ReaderPreferencesState {
  return { ...DEFAULT_READER_PREFERENCES };
}

function clampNumber(value: unknown, min: number, max: number, fallback: number) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return fallback;
  }

  return Math.min(Math.max(value, min), max);
}

function normalizeBookshelfPreferences(input?: Partial<BookshelfPreferencesState>): BookshelfPreferencesState {
  const groupId = input?.groupId;
  const page = input?.page;
  const pageSize = input?.pageSize;

  return {
    sort: input?.sort === "recent_read" || input?.sort === "title" ? input.sort : "created_at",
    search: typeof input?.search === "string" ? input.search.trim().slice(0, 200) : "",
    groupId: typeof groupId === "number" && Number.isInteger(groupId) && groupId >= 1 ? groupId : null,
    page: typeof page === "number" && Number.isInteger(page) && page >= 1 ? page : 1,
    pageSize: typeof pageSize === "number" && Number.isInteger(pageSize) && pageSize >= 1 && pageSize <= 100
      ? pageSize
      : null,
  };
}

function normalizeReaderPreferences(input?: Partial<ReaderPreferencesState>): ReaderPreferencesState {
  return {
    fontSize: Math.round(clampNumber(input?.fontSize, 15, 32, DEFAULT_READER_PREFERENCES.fontSize)),
    lineHeight: Number(clampNumber(input?.lineHeight, 1.45, 2.6, DEFAULT_READER_PREFERENCES.lineHeight).toFixed(2)),
    letterSpacing: Number(clampNumber(input?.letterSpacing, 0, 2, DEFAULT_READER_PREFERENCES.letterSpacing).toFixed(2)),
    paragraphSpacing: Number(
      clampNumber(input?.paragraphSpacing, 0, 2.5, DEFAULT_READER_PREFERENCES.paragraphSpacing).toFixed(2),
    ),
    contentWidth: Math.round(clampNumber(input?.contentWidth, 56, 96, DEFAULT_READER_PREFERENCES.contentWidth)),
    theme: input?.theme === "dark" ? "dark" : "light",
  };
}

function fromApiBookshelfPreferences(input: ApiBookshelfPreferences): BookshelfPreferencesState {
  return normalizeBookshelfPreferences({
    sort: input.sort,
    search: input.search,
    groupId: input.group_id,
    page: input.page,
    pageSize: input.page_size,
  });
}

function fromApiReaderPreferences(input: ApiReaderPreferences): ReaderPreferencesState {
  return normalizeReaderPreferences({
    fontSize: input.font_size,
    lineHeight: input.line_height,
    letterSpacing: input.letter_spacing,
    paragraphSpacing: input.paragraph_spacing,
    contentWidth: input.content_width,
    theme: input.theme,
  });
}

function toApiBookshelfPatch(input: Partial<BookshelfPreferencesState>): ApiBookshelfPreferencesPatch {
  const patch: ApiBookshelfPreferencesPatch = {};

  if (input.sort !== undefined) {
    patch.sort = input.sort;
  }
  if (input.search !== undefined) {
    patch.search = input.search;
  }
  if (input.groupId !== undefined) {
    patch.group_id = input.groupId;
  }
  if (input.page !== undefined) {
    patch.page = input.page;
  }
  if (input.pageSize !== undefined) {
    patch.page_size = input.pageSize;
  }

  return patch;
}

function toApiReaderPatch(input: Partial<ReaderPreferencesState>): ApiReaderPreferencesPatch {
  const patch: ApiReaderPreferencesPatch = {};

  if (input.fontSize !== undefined) {
    patch.font_size = input.fontSize;
  }
  if (input.lineHeight !== undefined) {
    patch.line_height = input.lineHeight;
  }
  if (input.letterSpacing !== undefined) {
    patch.letter_spacing = input.letterSpacing;
  }
  if (input.paragraphSpacing !== undefined) {
    patch.paragraph_spacing = input.paragraphSpacing;
  }
  if (input.contentWidth !== undefined) {
    patch.content_width = input.contentWidth;
  }
  if (input.theme !== undefined) {
    patch.theme = input.theme;
  }

  return patch;
}

function mergePatch(
  base: ApiUserPreferencesPatchRequest,
  patch: ApiUserPreferencesPatchRequest,
): ApiUserPreferencesPatchRequest {
  return {
    bookshelf: patch.bookshelf ? { ...(base.bookshelf || {}), ...patch.bookshelf } : base.bookshelf,
    reader: patch.reader ? { ...(base.reader || {}), ...patch.reader } : base.reader,
  };
}

function isEmptyPatch(patch: ApiUserPreferencesPatchRequest) {
  return !patch.bookshelf && !patch.reader;
}

function loadLegacyReaderPreferences(): ReaderPreferencesState | null {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const raw = window.localStorage.getItem(LEGACY_READER_PREFERENCES_KEY);
    if (!raw) {
      return null;
    }

    const parsed = JSON.parse(raw) as Partial<ReaderPreferencesState> & {
      fontSize?: number;
      lineHeight?: number;
      letterSpacing?: number;
      paragraphSpacing?: number;
      contentWidth?: number;
      theme?: "light" | "dark";
    };

    return normalizeReaderPreferences({
      fontSize: parsed.fontSize,
      lineHeight: parsed.lineHeight,
      letterSpacing: parsed.letterSpacing,
      paragraphSpacing: parsed.paragraphSpacing,
      contentWidth: parsed.contentWidth,
      theme: parsed.theme,
    });
  } catch {
    return null;
  }
}

export const usePreferencesStore = defineStore("preferences", {
  state: (): PreferencesState => ({
    version: 1,
    bookshelf: createDefaultBookshelfPreferences(),
    reader: createDefaultReaderPreferences(),
    initialized: false,
    loading: false,
    saving: false,
    hasSavedPreferences: false,
    errorMessage: null,
    saveErrorMessage: null,
    bootstrapPromise: null,
  }),
  actions: {
    async ensureReady() {
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
      this.loading = true;
      this.errorMessage = null;

      try {
        const response = await preferencesApi.get();
        this.applyResponse(response);

        if (!response.has_saved_preferences) {
          const legacyReaderPreferences = loadLegacyReaderPreferences();
          if (legacyReaderPreferences) {
            this.reader = legacyReaderPreferences;
            this.queuePatch(
              {
                reader: toApiReaderPatch(legacyReaderPreferences),
              },
              0,
            );
            await this.flushPendingPatch();
          } else {
            this.persistLegacyReaderPreferences();
          }
        } else {
          this.persistLegacyReaderPreferences();
        }
      } catch (error) {
        this.errorMessage = getErrorMessage(error);
        this.version = 1;
        this.bookshelf = createDefaultBookshelfPreferences();
        this.reader = loadLegacyReaderPreferences() ?? createDefaultReaderPreferences();
        this.hasSavedPreferences = false;
        this.persistLegacyReaderPreferences();
      } finally {
        this.loading = false;
        this.initialized = true;
      }
    },
    applyResponse(response: ApiUserPreferencesResponse) {
      this.version = response.preferences.version || 1;
      this.bookshelf = fromApiBookshelfPreferences(response.preferences.bookshelf);
      this.reader = fromApiReaderPreferences(response.preferences.reader);
      this.hasSavedPreferences = response.has_saved_preferences;
      this.saveErrorMessage = null;
    },
    patchBookshelf(input: Partial<BookshelfPreferencesState>, debounceMs = SAVE_DEBOUNCE_MS) {
      const nextValue = normalizeBookshelfPreferences({
        ...this.bookshelf,
        ...input,
      });

      const changedPatch: Partial<BookshelfPreferencesState> = {};
      if (nextValue.sort !== this.bookshelf.sort) {
        changedPatch.sort = nextValue.sort;
      }
      if (nextValue.search !== this.bookshelf.search) {
        changedPatch.search = nextValue.search;
      }
      if (nextValue.groupId !== this.bookshelf.groupId) {
        changedPatch.groupId = nextValue.groupId;
      }
      if (nextValue.page !== this.bookshelf.page) {
        changedPatch.page = nextValue.page;
      }
      if (nextValue.pageSize !== this.bookshelf.pageSize) {
        changedPatch.pageSize = nextValue.pageSize;
      }

      if (Object.keys(changedPatch).length === 0) {
        return;
      }

      this.bookshelf = nextValue;
      this.queuePatch(
        {
          bookshelf: toApiBookshelfPatch(changedPatch),
        },
        debounceMs,
      );
    },
    patchReader(input: Partial<ReaderPreferencesState>, debounceMs = SAVE_DEBOUNCE_MS) {
      const nextValue = normalizeReaderPreferences({
        ...this.reader,
        ...input,
      });

      const changedPatch: Partial<ReaderPreferencesState> = {};
      if (nextValue.fontSize !== this.reader.fontSize) {
        changedPatch.fontSize = nextValue.fontSize;
      }
      if (nextValue.lineHeight !== this.reader.lineHeight) {
        changedPatch.lineHeight = nextValue.lineHeight;
      }
      if (nextValue.letterSpacing !== this.reader.letterSpacing) {
        changedPatch.letterSpacing = nextValue.letterSpacing;
      }
      if (nextValue.paragraphSpacing !== this.reader.paragraphSpacing) {
        changedPatch.paragraphSpacing = nextValue.paragraphSpacing;
      }
      if (nextValue.contentWidth !== this.reader.contentWidth) {
        changedPatch.contentWidth = nextValue.contentWidth;
      }
      if (nextValue.theme !== this.reader.theme) {
        changedPatch.theme = nextValue.theme;
      }

      if (Object.keys(changedPatch).length === 0) {
        return;
      }

      this.reader = nextValue;
      this.persistLegacyReaderPreferences();
      this.queuePatch(
        {
          reader: toApiReaderPatch(changedPatch),
        },
        debounceMs,
      );
    },
    queuePatch(patch: ApiUserPreferencesPatchRequest, debounceMs = SAVE_DEBOUNCE_MS) {
      pendingPatch = mergePatch(pendingPatch, patch);
      this.saveErrorMessage = null;

      if (saveTimer) {
        clearTimeout(saveTimer);
        saveTimer = null;
      }

      if (debounceMs <= 0) {
        void this.flushPendingPatch();
        return;
      }

      saveTimer = window.setTimeout(() => {
        saveTimer = null;
        void this.flushPendingPatch();
      }, debounceMs);
    },
    async flushPendingPatch() {
      if (saveTimer) {
        clearTimeout(saveTimer);
        saveTimer = null;
      }

      if (isEmptyPatch(pendingPatch)) {
        return;
      }

      if (savePromise) {
        await savePromise;
        return;
      }

      const patchToSend = pendingPatch;
      pendingPatch = {};
      this.saving = true;

      savePromise = preferencesApi.patch(patchToSend)
        .then((response) => {
          this.applyResponse(response);
          this.persistLegacyReaderPreferences();
        })
        .catch((error) => {
          this.saveErrorMessage = getErrorMessage(error);
          pendingPatch = mergePatch(patchToSend, pendingPatch);
        })
        .finally(() => {
          this.saving = false;
          savePromise = null;
        });

      await savePromise;
    },
    persistLegacyReaderPreferences() {
      if (typeof window === "undefined") {
        return;
      }

      window.localStorage.setItem(
        LEGACY_READER_PREFERENCES_KEY,
        JSON.stringify(this.reader),
      );
    },
    resetState() {
      this.version = 1;
      this.bookshelf = createDefaultBookshelfPreferences();
      this.reader = createDefaultReaderPreferences();
      this.initialized = false;
      this.loading = false;
      this.saving = false;
      this.hasSavedPreferences = false;
      this.errorMessage = null;
      this.saveErrorMessage = null;
      this.bootstrapPromise = null;
      pendingPatch = {};
      if (saveTimer) {
        clearTimeout(saveTimer);
        saveTimer = null;
      }
    },
  },
});
