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
