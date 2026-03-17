export interface ApiFieldError {
  loc: Array<string | number>;
  msg: string;
  type: string;
}

export interface ApiErrorResponse {
  success?: false;
  detail?: string | ApiFieldError[];
  error?: {
    code?: string;
    message: string;
    details?: unknown;
  };
}

export interface LoginPayload {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface User {
  id: number;
  username: string;
  created_at: string;
}

export interface ChapterRule {
  id: number;
  user_id: number | null;
  rule_name: string;
  regex_pattern: string;
  flags: string;
  description: string | null;
  is_builtin: boolean;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface ChapterRulePayload {
  rule_name: string;
  regex_pattern: string;
  flags: string;
  description: string | null;
  is_default: boolean;
}

export interface ChapterRuleTestPayload {
  book_id?: number;
  text?: string;
  regex_pattern: string;
  flags: string;
}

export interface ChapterRuleTestMatchItem {
  text: string;
  start: number;
  end: number;
}

export interface ChapterRuleTestResponse {
  matched: boolean;
  count: number;
  items: ChapterRuleTestMatchItem[];
}

export interface BookGroupSummary {
  id: number;
  name: string;
}

export interface BookGroup extends BookGroupSummary {
  book_count: number;
  created_at: string;
  updated_at: string;
}

export interface BookGroupPayload {
  name: string;
}

export interface BookGroupAssignmentPayload {
  group_ids: number[];
}

export type BookSortKey = "created_at" | "recent_read" | "title";
export type LibrarySourceKind = "local" | "online";

export interface LibraryBookSourceMeta {
  source_id: number | null;
  remote_book_id: string | null;
  detail_url: string | null;
}

export interface LocalFileMeta {
  file_name: string;
  file_path: string;
  encoding: string;
}

export interface OnlineBookMeta {
  source_id: number;
  source_name: string;
  detail_url: string;
  remote_book_id: string | null;
  latest_catalog_fetched_at: string | null;
}

export interface LibraryBookSummary {
  library_id: string;
  source_kind: LibrarySourceKind;
  source_label: string;
  entity_id: number;
  title: string;
  author: string | null;
  cover_url: string | null;
  total_chapters: number | null;
  total_words: number | null;
  progress_percent: number | null;
  recent_read_at: string | null;
  created_at: string;
  updated_at: string;
  groups: BookGroupSummary[];
  source_meta?: LibraryBookSourceMeta | null;
}

export interface LibraryBookDetail {
  source_kind: LibrarySourceKind;
  entity_id: number;
  library_book_id: string;
  source_label: string;
  title: string;
  author: string | null;
  description: string | null;
  cover_url: string | null;
  total_chapters: number | null;
  total_words: number | null;
  recent_read_at: string | null;
  progress_percent: number | null;
  created_at: string;
  updated_at: string;
  groups: BookGroupSummary[];
  chapter_rule: ChapterRule | null;
  local_file: LocalFileMeta | null;
  online_meta: OnlineBookMeta | null;
}

export interface LibraryBooksQuery {
  q?: string;
  sort_by?: "created_at" | "recent_read_at" | "title";
  sort_order?: "asc" | "desc";
  source_kind?: LibrarySourceKind;
}

export interface BookShelfItem {
  id: number;
  title: string;
  author: string | null;
  total_chapters: number;
  total_words: number;
  last_read_at: string | null;
  recent_read_at: string | null;
  progress_percent: number | null;
  cover_url: string | null;
  created_at: string;
  updated_at: string;
  groups: BookGroupSummary[];
}

export interface BookDetail {
  id: number;
  user_id: number;
  title: string;
  author: string | null;
  description: string | null;
  encoding: string;
  total_words: number;
  total_chapters: number;
  chapter_rule_id: number | null;
  file_name: string;
  file_path: string;
  cover_url: string | null;
  recent_read_at: string | null;
  progress_percent: number | null;
  created_at: string;
  updated_at: string;
  chapter_rule?: ChapterRule | null;
  groups: BookGroupSummary[];
}

export interface BookMetadataPayload {
  title?: string | null;
  author?: string | null;
  description?: string | null;
}

export interface BookChapter {
  id: number;
  book_id: number;
  chapter_index: number;
  chapter_title: string;
  start_offset: number;
  end_offset: number;
  created_at: string;
}

export interface BookChapterContent {
  book_id: number;
  chapter_index: number;
  chapter_title: string;
  start_offset: number;
  end_offset: number;
  content: string;
}

export interface OnlineBookDetail {
  id: number;
  user_id: number;
  source_id: number;
  source_name: string;
  title: string;
  author: string | null;
  cover_url: string | null;
  description: string | null;
  remote_book_id: string | null;
  detail_url: string;
  total_chapters: number | null;
  latest_catalog_fetched_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface OnlineBookCatalogEntry {
  id: number;
  online_book_id: number;
  chapter_index: number;
  chapter_title: string;
  chapter_url: string;
  created_at: string;
  updated_at: string;
}

export interface OnlineBookChapterContent {
  online_book_id: number;
  chapter_index: number;
  chapter_title: string;
  content: string;
  content_length: number;
  source_url: string | null;
}

export type OnlineSourceValidationStatus = "unchecked" | "valid" | "invalid";

export interface OnlineSourceSummary {
  id: number;
  user_id: number;
  name: string;
  description: string | null;
  enabled: boolean;
  base_url: string;
  validation_status: OnlineSourceValidationStatus;
  validation_errors: string[];
  last_checked_at: string | null;
  created_at: string;
  updated_at: string;
}

export type LegadoIssueSeverity = "error" | "warning";
export type LegadoIssueStage = "source" | "search" | "detail" | "catalog" | "content" | null;

export interface LegadoImportIssue {
  code: string;
  error_code: string;
  message: string;
  field?: string | null;
  severity: LegadoIssueSeverity;
  source_path?: string | null;
  stage?: LegadoIssueStage;
  field_name?: string | null;
  raw_value?: unknown | null;
  normalized_value?: unknown | null;
}

export interface LegadoMappedSource {
  name: string;
  description: string | null;
  enabled: boolean;
  base_url: string;
  definition: unknown;
}

export interface LegadoImportResult {
  is_valid: boolean;
  mapped_source: LegadoMappedSource | null;
  source_id: number | null;
  errors: LegadoImportIssue[];
  warnings: LegadoImportIssue[];
  ignored_fields: string[];
  unsupported_fields: string[];
}

export interface ReadingProgress {
  id: number;
  user_id: number;
  book_id: number;
  chapter_index: number;
  char_offset: number;
  percent: number;
  updated_at: string;
}

export interface ReadingProgressPayload {
  chapter_index: number;
  char_offset: number;
  percent: number;
  updated_at: string;
}

export interface BookReparseChapterSummary {
  chapter_index: number;
  chapter_title: string;
  start_offset: number;
  end_offset: number;
}

export interface BookReparseResponse {
  book_id: number;
  chapter_rule_id: number;
  total_chapters: number;
  chapters: BookReparseChapterSummary[];
}

export interface ApiBookshelfPreferences {
  sort: BookSortKey;
  search: string;
  group_id: number | null;
  page: number;
  page_size: number | null;
}

export interface ApiReaderPreferences {
  font_size: number;
  line_height: number;
  letter_spacing: number;
  paragraph_spacing: number;
  content_width: number;
  theme: "light" | "dark";
}

export interface ApiUserPreferencesDocument {
  version: number;
  bookshelf: ApiBookshelfPreferences;
  reader: ApiReaderPreferences;
}

export interface ApiBookshelfPreferencesPatch {
  sort?: BookSortKey;
  search?: string | null;
  group_id?: number | null;
  page?: number;
  page_size?: number | null;
}

export interface ApiReaderPreferencesPatch {
  font_size?: number;
  line_height?: number;
  letter_spacing?: number;
  paragraph_spacing?: number;
  content_width?: number;
  theme?: "light" | "dark";
}

export interface ApiUserPreferencesPatchRequest {
  bookshelf?: ApiBookshelfPreferencesPatch;
  reader?: ApiReaderPreferencesPatch;
}

export interface ApiUserPreferencesResponse {
  has_saved_preferences: boolean;
  preferences: ApiUserPreferencesDocument;
}
