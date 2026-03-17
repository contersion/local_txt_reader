import { apiClient } from "./client";
import type { BookSortKey, LibraryBookSummary, LibraryBooksQuery } from "../types/api";


interface LibraryListParams {
  q?: string;
  sort?: BookSortKey;
  sourceKind?: "local" | "online" | null;
}

function toLibraryQuery(params: LibraryListParams = {}): LibraryBooksQuery {
  const sort = params.sort || "created_at";

  return {
    q: params.q,
    sort_by: sort === "recent_read" ? "recent_read_at" : sort,
    sort_order: sort === "title" ? "asc" : "desc",
    source_kind: params.sourceKind || undefined,
  };
}

export const libraryApi = {
  list(params: LibraryListParams = {}) {
    const query = toLibraryQuery(params);
    return apiClient.get<LibraryBookSummary[]>("/api/library/books", {
      query: {
        q: query.q,
        sort_by: query.sort_by,
        sort_order: query.sort_order,
        source_kind: query.source_kind,
      },
    });
  },
};
