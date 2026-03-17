import { computed } from "vue";

import { booksApi } from "../api/books";
import { getErrorMessage, ApiError } from "../api/client";
import { onlineBooksApi } from "../api/online-books";
import type {
  BookChapter,
  BookDetail,
  LibraryBookDetail,
  OnlineBookCatalogEntry,
  OnlineBookDetail,
  ReadingProgress,
} from "../types/api";
import { parseLibraryBookId } from "../utils/library-id";


export interface BookDetailSourcePayload {
  detail: LibraryBookDetail;
  catalog: BookChapter[];
  progress: ReadingProgress | null;
  sourceKind: "local" | "online";
  isLocal: boolean;
  actions: {
    canEditMetadata: boolean;
    canUploadCover: boolean;
    canReparseCatalog: boolean;
  };
}

function toLocalCatalogItem(item: BookChapter): BookChapter {
  return item;
}

function toOnlineCatalogItem(item: OnlineBookCatalogEntry): BookChapter {
  return {
    id: item.id,
    book_id: item.online_book_id,
    chapter_index: item.chapter_index,
    chapter_title: item.chapter_title,
    start_offset: 0,
    end_offset: 0,
    created_at: item.created_at,
  };
}

function toLocalDetail(detail: BookDetail): LibraryBookDetail {
  return {
    source_kind: "local",
    entity_id: detail.id,
    library_book_id: `local:${detail.id}`,
    source_label: "本地TXT",
    title: detail.title,
    author: detail.author,
    description: detail.description,
    cover_url: detail.cover_url,
    total_chapters: detail.total_chapters,
    total_words: detail.total_words,
    recent_read_at: detail.recent_read_at,
    progress_percent: detail.progress_percent,
    created_at: detail.created_at,
    updated_at: detail.updated_at,
    groups: detail.groups,
    chapter_rule: detail.chapter_rule || null,
    local_file: {
      file_name: detail.file_name,
      file_path: detail.file_path,
      encoding: detail.encoding,
    },
    online_meta: null,
  };
}

function toOnlineDetail(detail: OnlineBookDetail): LibraryBookDetail {
  return {
    source_kind: "online",
    entity_id: detail.id,
    library_book_id: `online:${detail.id}`,
    source_label: detail.source_name,
    title: detail.title,
    author: detail.author,
    description: detail.description,
    cover_url: detail.cover_url,
    total_chapters: detail.total_chapters,
    total_words: null,
    recent_read_at: null,
    progress_percent: null,
    created_at: detail.created_at,
    updated_at: detail.updated_at,
    groups: [],
    chapter_rule: null,
    local_file: null,
    online_meta: {
      source_id: detail.source_id,
      source_name: detail.source_name,
      detail_url: detail.detail_url,
      remote_book_id: detail.remote_book_id,
      latest_catalog_fetched_at: detail.latest_catalog_fetched_at,
    },
  };
}

async function loadLocalProgress(bookId: number) {
  try {
    return await booksApi.getProgress(bookId);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }

    throw error;
  }
}

async function loadOnlineProgress(onlineBookId: number) {
  try {
    return await onlineBooksApi.getProgress(onlineBookId);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }

    throw error;
  }
}

export function useBookDetailSource(libraryBookId: string) {
  const parsed = computed(() => parseLibraryBookId(libraryBookId));

  async function load(): Promise<BookDetailSourcePayload> {
    const { sourceKind, entityId } = parsed.value;

    if (sourceKind === "local") {
      const [detail, catalog, progress] = await Promise.all([
        booksApi.detail(entityId),
        booksApi.chapters(entityId),
        loadLocalProgress(entityId),
      ]);

      return {
        detail: toLocalDetail(detail),
        catalog: catalog.map(toLocalCatalogItem),
        progress,
        sourceKind,
        isLocal: true,
        actions: {
          canEditMetadata: true,
          canUploadCover: true,
          canReparseCatalog: true,
        },
      };
    }

    const [detail, catalog, progress] = await Promise.all([
      onlineBooksApi.detail(entityId),
      onlineBooksApi.catalog(entityId),
      loadOnlineProgress(entityId),
    ]);

    return {
      detail: toOnlineDetail(detail),
      catalog: catalog.map(toOnlineCatalogItem),
      progress,
      sourceKind,
      isLocal: false,
      actions: {
        canEditMetadata: false,
        canUploadCover: false,
        canReparseCatalog: false,
      },
    };
  }

  return {
    parsed,
    load,
    getErrorMessage,
  };
}
