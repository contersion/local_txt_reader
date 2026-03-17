import { computed } from "vue";

import { booksApi } from "../api/books";
import { ApiError } from "../api/client";
import { onlineBooksApi } from "../api/online-books";
import type {
  BookChapter,
  BookChapterContent,
  OnlineBookCatalogEntry,
  OnlineBookChapterContent,
  ReadingProgress,
  ReadingProgressPayload,
} from "../types/api";
import { parseLibraryBookId } from "../utils/library-id";


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

function toOnlineChapterContent(onlineBookId: number, content: OnlineBookChapterContent): BookChapterContent {
  return {
    book_id: onlineBookId,
    chapter_index: content.chapter_index,
    chapter_title: content.chapter_title,
    start_offset: 0,
    end_offset: content.content_length,
    content: content.content,
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

export function useReaderSource(libraryBookId: string) {
  const parsed = computed(() => parseLibraryBookId(libraryBookId));

  async function loadCatalog() {
    const { sourceKind, entityId } = parsed.value;
    if (sourceKind === "local") {
      return (await booksApi.chapters(entityId)).map(toLocalCatalogItem);
    }
    return (await onlineBooksApi.catalog(entityId)).map(toOnlineCatalogItem);
  }

  async function loadChapterContent(chapterIndex: number) {
    const { sourceKind, entityId } = parsed.value;
    if (sourceKind === "local") {
      return booksApi.chapterContent(entityId, chapterIndex);
    }
    const content = await onlineBooksApi.chapterContent(entityId, chapterIndex);
    return toOnlineChapterContent(entityId, content);
  }

  async function loadProgress() {
    const { sourceKind, entityId } = parsed.value;
    if (sourceKind === "local") {
      return loadLocalProgress(entityId);
    }
    return loadOnlineProgress(entityId);
  }

  async function saveProgress(payload: ReadingProgressPayload): Promise<ReadingProgress> {
    const { sourceKind, entityId } = parsed.value;
    if (sourceKind === "local") {
      return booksApi.saveProgress(entityId, payload);
    }
    return onlineBooksApi.saveProgress(entityId, payload);
  }

  async function loadDisplayTitle() {
    const { sourceKind, entityId } = parsed.value;
    if (sourceKind === "local") {
      const detail = await booksApi.detail(entityId);
      return detail.title;
    }
    const detail = await onlineBooksApi.detail(entityId);
    return detail.title;
  }

  return {
    parsed,
    loadCatalog,
    loadChapterContent,
    loadProgress,
    saveProgress,
    loadDisplayTitle,
  };
}
