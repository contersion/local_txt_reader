import { apiClient } from "./client";
import type {
  BookGroupAssignmentPayload,
  BookGroupSummary,
  OnlineBookCatalogEntry,
  OnlineBookChapterContent,
  OnlineBookDetail,
  ReadingProgress,
  ReadingProgressPayload,
} from "../types/api";


export const onlineBooksApi = {
  detail(onlineBookId: number) {
    return apiClient.get<OnlineBookDetail>(`/api/online-books/${onlineBookId}`);
  },
  catalog(onlineBookId: number) {
    return apiClient.get<OnlineBookCatalogEntry[]>(`/api/online-books/${onlineBookId}/catalog`);
  },
  chapterContent(onlineBookId: number, chapterIndex: number) {
    return apiClient.get<OnlineBookChapterContent>(`/api/online-books/${onlineBookId}/chapters/${chapterIndex}`);
  },
  getGroups(onlineBookId: number) {
    return apiClient.get<BookGroupSummary[]>(`/api/online-books/${onlineBookId}/groups`);
  },
  updateGroups(onlineBookId: number, payload: BookGroupAssignmentPayload) {
    return apiClient.put<BookGroupSummary[]>(`/api/online-books/${onlineBookId}/groups`, payload);
  },
  getProgress(onlineBookId: number) {
    return apiClient.get<ReadingProgress>(`/api/online-books/${onlineBookId}/progress`);
  },
  saveProgress(onlineBookId: number, payload: ReadingProgressPayload) {
    return apiClient.put<ReadingProgress>(`/api/online-books/${onlineBookId}/progress`, payload);
  },
};
