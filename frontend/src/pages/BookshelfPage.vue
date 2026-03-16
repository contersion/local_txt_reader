<template>
  <div class="bookshelf-page">
    <header class="bookshelf-page__header">
      <div class="bookshelf-page__title-wrap">
        <h1 class="bookshelf-page__title">书架</h1>
        <span class="bookshelf-page__count">{{ displayedBooks.length }}</span>
      </div>

      <div class="bookshelf-page__header-actions">
        <n-button quaternary size="small" :loading="loading" @click="handleRefresh">刷新</n-button>
        <n-button quaternary size="small" :loading="groupMutationPending" @click="groupManagerVisible = true">
          分组管理
        </n-button>
        <n-button quaternary size="small" @click="toggleEditMode">
          {{ isEditMode ? "完成" : "编辑" }}
        </n-button>
        <n-upload
          ref="uploadRef"
          accept=".txt,text/plain"
          :show-file-list="false"
          :max="1"
          :custom-request="handleUpload"
        >
          <n-button type="primary" secondary size="small" :loading="uploading">上传 TXT</n-button>
        </n-upload>
      </div>
    </header>

    <section class="bookshelf-page__controls">
      <div class="bookshelf-page__filter-bar">
        <div class="bookshelf-page__tabs-wrap">
          <div class="bookshelf-page__tabs" role="tablist" aria-label="书架分组筛选">
            <button
              v-for="filter in filterOptions"
              :key="filter.key"
              type="button"
              class="bookshelf-page__tab"
              :class="{ 'bookshelf-page__tab--active': activeFilter === filter.key }"
              :aria-selected="activeFilter === filter.key"
              @click="activeFilter = filter.key"
            >
              {{ filter.label }}
            </button>
          </div>
        </div>

        <div class="bookshelf-page__filter-actions">
          <n-select
            v-model:value="sortKey"
            size="small"
            class="bookshelf-page__sort"
            :options="sortOptions"
            :consistent-menu-width="false"
          />

          <div class="bookshelf-page__search">
            <n-input
              v-model:value="searchKeyword"
              clearable
              size="small"
              placeholder="搜索书名"
              @keydown.enter.prevent="handleSearch"
              @clear="handleClearSearch"
            />
            <n-button secondary size="small" :loading="loading" @click="handleSearch">搜索</n-button>
          </div>
        </div>
      </div>
    </section>

    <n-alert v-if="errorMessage" type="error" :show-icon="false" class="bookshelf-page__alert">
      {{ errorMessage }}
    </n-alert>

    <n-alert v-if="groupWarningMessage" type="warning" :show-icon="false" class="bookshelf-page__alert">
      {{ groupWarningMessage }}
    </n-alert>

    <section v-if="loading" class="bookshelf-list bookshelf-list--loading" aria-label="加载中的书架">
      <article v-for="index in 6" :key="index" class="bookshelf-item bookshelf-item--loading">
        <div class="bookshelf-item__cover bookshelf-item__cover--loading"></div>
        <div class="bookshelf-item__body">
          <n-skeleton text :repeat="3" />
          <n-skeleton style="margin-top: 8px;" text :repeat="2" />
          <n-skeleton style="margin-top: 8px;" text :repeat="2" />
        </div>
      </article>
    </section>

    <n-empty v-else-if="displayedBooks.length === 0" :description="emptyDescription" class="bookshelf-page__empty">
      <template #extra>
        <span class="bookshelf-page__empty-tip">上传一本 TXT 后，书架会自动刷新。</span>
      </template>
    </n-empty>

    <section v-else class="bookshelf-list" aria-label="书籍列表">
      <article
        v-for="book in displayedBooks"
        :key="book.id"
        class="bookshelf-item"
        @click="goToDetail(book.id)"
      >
        <div class="bookshelf-item__cover" :class="{ 'bookshelf-item__cover--filled': !!book.cover_url }" aria-hidden="true">
          <img
            v-if="resolveCover(book.cover_url)"
            class="bookshelf-item__cover-image"
            :src="resolveCover(book.cover_url) || undefined"
            :alt="`${book.title} 封面`"
            loading="lazy"
          />
          <template v-else>
            <span class="bookshelf-item__cover-type">TXT</span>
            <strong class="bookshelf-item__cover-letter">{{ getCoverLetter(book.title) }}</strong>
            <span class="bookshelf-item__cover-text">无封面</span>
          </template>
        </div>

        <div class="bookshelf-item__body">
          <div class="bookshelf-item__header-block">
            <div class="bookshelf-item__title-row">
              <h2 class="bookshelf-item__title">{{ book.title }}</h2>
              <span class="bookshelf-item__badge">{{ continueLabel(book) }}</span>
            </div>

            <div class="bookshelf-item__status-row">
              <span>{{ formatReadingLabel(book) }}</span>
              <span>{{ formatRecentLabel(book.recent_read_at ?? book.last_read_at) }}</span>
            </div>
          </div>

          <div class="bookshelf-item__facts">
            <span>{{ book.author || "作者未填写" }}</span>
            <span>共 {{ formatNumber(book.total_chapters) }} 章</span>
            <span>{{ formatWordCount(book.total_words) }}</span>
            <span>收录于 {{ formatDate(book.created_at) }}</span>
          </div>

          <div class="bookshelf-item__groups">
            <n-tag
              v-for="group in book.groups"
              :key="`${book.id}-${group.id}`"
              size="small"
              round
              :bordered="false"
              type="warning"
            >
              {{ group.name }}
            </n-tag>
          </div>

          <div class="bookshelf-item__footer">
            <div class="bookshelf-item__progress">
              <div class="bookshelf-item__progress-head">
                <span>阅读进度</span>
                <strong>{{ formatProgress(book.progress_percent) }}</strong>
              </div>
              <n-progress
                type="line"
                :percentage="normalizeProgress(book.progress_percent)"
                :show-indicator="false"
                :height="6"
                rail-color="rgba(109, 90, 74, 0.12)"
                color="var(--primary-color)"
              />
            </div>

            <div class="bookshelf-item__actions">
              <n-button
                text
                type="primary"
                class="bookshelf-item__action bookshelf-item__action--primary"
                :loading="continuingBookId === book.id"
                @click.stop="handleContinue(book)"
              >
                {{ continueLabel(book) }}
              </n-button>
              <n-button quaternary size="small" class="bookshelf-item__action" @click.stop="goToDetail(book.id)">
                详情
              </n-button>
              <n-button quaternary size="small" class="bookshelf-item__action" @click.stop="openBookGroupSelector(book)">
                管理分组
              </n-button>
              <n-popconfirm v-if="isEditMode" @positive-click="() => handleDelete(book)">
                <template #trigger>
                  <n-button
                    quaternary
                    size="small"
                    type="error"
                    class="bookshelf-item__action"
                    :loading="deletingBookId === book.id"
                    @click.stop
                  >
                    删除
                  </n-button>
                </template>
                删除后将同时移除本地书籍文件，确认继续吗？
              </n-popconfirm>
            </div>
          </div>
        </div>
      </article>
    </section>

    <book-group-manager-modal
      v-model:show="groupManagerVisible"
      :groups="groups"
      :busy="groupMutationPending"
      @create="handleCreateGroup"
      @rename="handleRenameGroup"
      @delete="handleDeleteGroup"
    />

    <book-group-selector-modal
      v-model:show="groupSelectorVisible"
      :book-title="managingBook?.title || ''"
      :groups="groups"
      :selected-group-ids="selectedGroupIds"
      :submitting="bookGroupsSubmitting"
      @submit="handleSubmitBookGroups"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import {
  NAlert,
  NButton,
  NEmpty,
  NInput,
  NPopconfirm,
  NProgress,
  NSelect,
  NSkeleton,
  NTag,
  NUpload,
  useMessage,
  type UploadCustomRequestOptions,
  type UploadInst,
} from "naive-ui";
import { useRouter } from "vue-router";

import { bookGroupsApi } from "../api/book-groups";
import { booksApi } from "../api/books";
import { resolveApiAssetUrl, ApiError, getErrorMessage } from "../api/client";
import BookGroupManagerModal from "../components/BookGroupManagerModal.vue";
import BookGroupSelectorModal from "../components/BookGroupSelectorModal.vue";
import type { BookGroup, BookShelfItem, BookSortKey } from "../types/api";
import { usePreferencesStore } from "../stores/preferences";
import { clampPercentage, formatDateTime, formatNumber, formatPercent, formatWordCount } from "../utils/format";

const router = useRouter();
const message = useMessage();
const preferencesStore = usePreferencesStore();
const BOOK_METADATA_UPDATED_EVENT = "books:metadata-updated";
const uploadRef = ref<UploadInst | null>(null);
const books = ref<BookShelfItem[]>([]);
const groups = ref<BookGroup[]>([]);
const searchKeyword = ref(preferencesStore.bookshelf.search);
const appliedSearch = ref(preferencesStore.bookshelf.search);
const loading = ref(false);
const uploading = ref(false);
const errorMessage = ref<string | null>(null);
const groupWarningMessage = ref<string | null>(null);
const deletingBookId = ref<number | null>(null);
const continuingBookId = ref<number | null>(null);
const isEditMode = ref(false);
const activeFilter = ref(getFilterKeyFromGroupId(preferencesStore.bookshelf.groupId));
const sortKey = ref<BookSortKey>(preferencesStore.bookshelf.sort);
const groupManagerVisible = ref(false);
const groupSelectorVisible = ref(false);
const managingBook = ref<BookShelfItem | null>(null);
const selectedGroupIds = ref<number[]>([]);
const groupMutationPending = ref(false);
const bookGroupsSubmitting = ref(false);

const sortOptions = [
  { label: "按收录时间", value: "created_at" },
  { label: "按最近阅读", value: "recent_read" },
  { label: "按书名", value: "title" },
] satisfies Array<{ label: string; value: BookSortKey }>;

const filterOptions = computed(() => {
  return [
    { key: "all", label: "全部" },
    ...groups.value.map((group) => ({ key: `group:${group.id}`, label: group.name })),
  ];
});

const displayedBooks = computed(() => books.value);

const emptyDescription = computed(() => {
  if (appliedSearch.value.trim()) {
    return "没有找到匹配的书籍，试试更短的关键词。";
  }

  if (getActiveGroupId(activeFilter.value) !== null) {
    return "当前分组下还没有书籍。";
  }

  return "书架还是空的，先上传一本 TXT 开始吧。";
});

watch(groups, (currentGroups) => {
  const groupId = getActiveGroupId(activeFilter.value);
  if (groupId === null) {
    return;
  }

  if (!currentGroups.some((group) => group.id === groupId)) {
    activeFilter.value = "all";
    preferencesStore.patchBookshelf({
      groupId: null,
      page: 1,
    });
  }
});

watch(activeFilter, () => {
  preferencesStore.patchBookshelf({
    groupId: getActiveGroupId(activeFilter.value),
    page: 1,
  });
  void loadBooks(appliedSearch.value);
});

watch(sortKey, () => {
  preferencesStore.patchBookshelf({
    sort: sortKey.value,
    page: 1,
  });
  void loadBooks(appliedSearch.value);
});

function getFilterKeyFromGroupId(groupId: number | null) {
  return groupId ? `group:${groupId}` : "all";
}

function getActiveGroupId(filterKey: string) {
  if (!filterKey.startsWith("group:")) {
    return null;
  }

  const value = Number(filterKey.slice("group:".length));
  return Number.isFinite(value) ? value : null;
}

function normalizeProgress(value: number | null) {
  return Math.round(clampPercentage(value));
}

function formatProgress(value: number | null) {
  return formatPercent(value);
}

function formatDate(value: string | null) {
  return formatDateTime(value, "时间未知");
}

function formatRecentLabel(value: string | null) {
  return value ? `最近阅读 ${formatDateTime(value)}` : "最近阅读：未开始";
}

function formatReadingLabel(book: BookShelfItem) {
  const progress = clampPercentage(book.progress_percent);
  return progress > 0 ? `已读 ${formatPercent(progress)}` : "尚未开始阅读";
}

function getCoverLetter(title: string) {
  const normalized = title.trim();
  return normalized ? normalized.slice(0, 1).toUpperCase() : "T";
}

function continueLabel(book: BookShelfItem) {
  return clampPercentage(book.progress_percent) > 0 ? "继续阅读" : "开始阅读";
}

function resolveCover(coverUrl: string | null) {
  return resolveApiAssetUrl(coverUrl);
}

function resetUploadControl() {
  uploadRef.value?.clear();
}

async function loadBooks(search = appliedSearch.value.trim()) {
  loading.value = true;
  errorMessage.value = null;

  try {
    books.value = await booksApi.list({
      search: search || undefined,
      groupId: getActiveGroupId(activeFilter.value),
      sort: sortKey.value,
    });
  } catch (error) {
    books.value = [];
    errorMessage.value = getErrorMessage(error);
  } finally {
    loading.value = false;
  }
}

async function loadGroups() {
  groupWarningMessage.value = null;

  try {
    groups.value = await bookGroupsApi.list();
  } catch (error) {
    groups.value = [];
    groupWarningMessage.value = getErrorMessage(error);
  }
}

async function loadPage() {
  await Promise.all([loadBooks(appliedSearch.value), loadGroups()]);
}

function handleSearch() {
  const normalizedSearch = searchKeyword.value.trim();
  searchKeyword.value = normalizedSearch;
  appliedSearch.value = normalizedSearch;
  preferencesStore.patchBookshelf({
    search: normalizedSearch,
    page: 1,
  });
  void loadBooks(normalizedSearch);
}

function handleClearSearch() {
  searchKeyword.value = "";
  appliedSearch.value = "";
  preferencesStore.patchBookshelf({
    search: "",
    page: 1,
  });
  void loadBooks("");
}

function handleRefresh() {
  void loadPage();
}

function toggleEditMode() {
  isEditMode.value = !isEditMode.value;
}

function goToDetail(bookId: number) {
  void router.push({
    name: "book-detail",
    params: { bookId },
  });
}

async function handleContinue(book: BookShelfItem) {
  continuingBookId.value = book.id;

  try {
    const progress = await booksApi.getProgress(book.id);
    await router.push({
      name: "reader",
      params: {
        bookId: book.id,
        chapterIndex: progress.chapter_index,
      },
    });
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      await router.push({
        name: "reader",
        params: { bookId: book.id },
      });
      return;
    }

    message.error(getErrorMessage(error));
  } finally {
    continuingBookId.value = null;
  }
}

async function handleDelete(book: BookShelfItem) {
  deletingBookId.value = book.id;

  try {
    await booksApi.delete(book.id);
    message.success(`已删除《${book.title}》`);
    await Promise.all([loadBooks(appliedSearch.value), loadGroups()]);
  } catch (error) {
    message.error(getErrorMessage(error));
  } finally {
    deletingBookId.value = null;
  }
}

async function handleUpload(options: UploadCustomRequestOptions) {
  const file = options.file.file;

  if (!(file instanceof File)) {
    const error = new Error("未找到可上传的文件内容");
    options.onError?.();
    resetUploadControl();
    message.error(error.message);
    return;
  }

  uploading.value = true;

  try {
    await booksApi.upload(file);
    options.onFinish?.();
    message.success(`《${file.name}》上传成功`);
    await loadPage();
  } catch (error) {
    options.onError?.();
    message.error(getErrorMessage(error));
  } finally {
    uploading.value = false;
    resetUploadControl();
  }
}

async function handleCreateGroup(name: string) {
  groupMutationPending.value = true;

  try {
    await bookGroupsApi.create({ name });
    message.success("分组已创建");
    await loadGroups();
  } catch (error) {
    message.error(getErrorMessage(error));
  } finally {
    groupMutationPending.value = false;
  }
}

async function handleRenameGroup(payload: { groupId: number; name: string }) {
  groupMutationPending.value = true;

  try {
    await bookGroupsApi.update(payload.groupId, { name: payload.name });
    message.success("分组已重命名");
    await Promise.all([loadGroups(), loadBooks(appliedSearch.value)]);
  } catch (error) {
    message.error(getErrorMessage(error));
  } finally {
    groupMutationPending.value = false;
  }
}

async function handleDeleteGroup(groupId: number) {
  groupMutationPending.value = true;

  try {
    await bookGroupsApi.remove(groupId);
    message.success("分组已删除");
    await Promise.all([loadGroups(), loadBooks(appliedSearch.value)]);
  } catch (error) {
    message.error(getErrorMessage(error));
  } finally {
    groupMutationPending.value = false;
  }
}

async function openBookGroupSelector(book: BookShelfItem) {
  managingBook.value = book;
  selectedGroupIds.value = book.groups.map((group) => group.id);
  groupSelectorVisible.value = true;

  try {
    const currentGroups = await booksApi.getGroups(book.id);
    selectedGroupIds.value = currentGroups.map((group) => group.id);
  } catch (error) {
    message.warning(`未能刷新《${book.title}》的最新分组，先使用当前页面数据。${getErrorMessage(error)}`);
  }
}

async function handleSubmitBookGroups(groupIds: number[]) {
  if (!managingBook.value) {
    return;
  }

  bookGroupsSubmitting.value = true;

  try {
    await booksApi.updateGroups(managingBook.value.id, { group_ids: groupIds });
    message.success(`已更新《${managingBook.value.title}》的分组`);
    groupSelectorVisible.value = false;
    await Promise.all([loadBooks(appliedSearch.value), loadGroups()]);
  } catch (error) {
    message.error(getErrorMessage(error));
  } finally {
    bookGroupsSubmitting.value = false;
  }
}

function handleMetadataUpdated() {
  void loadBooks(appliedSearch.value);
}

onMounted(() => {
  if (typeof window !== "undefined") {
    window.addEventListener(BOOK_METADATA_UPDATED_EVENT, handleMetadataUpdated);
  }

  void loadPage();
});

onUnmounted(() => {
  if (typeof window !== "undefined") {
    window.removeEventListener(BOOK_METADATA_UPDATED_EVENT, handleMetadataUpdated);
  }
});
</script>

<style scoped>
.bookshelf-page {
  width: min(100%, 1720px);
  margin: 0 auto;
  display: grid;
  gap: 22px;
}

.bookshelf-page__header {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  align-items: center;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(109, 90, 74, 0.1);
}

.bookshelf-page__title-wrap {
  display: flex;
  gap: 10px;
  align-items: baseline;
}

.bookshelf-page__title {
  margin: 0;
  font-size: clamp(28px, 3vw, 38px);
  line-height: 1.08;
}

.bookshelf-page__count {
  color: var(--text-secondary);
  font-size: 16px;
  font-weight: 600;
}

.bookshelf-page__header-actions {
  display: flex;
  gap: 6px;
  align-items: center;
  flex-wrap: wrap;
}

.bookshelf-page__controls {
  display: grid;
  gap: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(109, 90, 74, 0.1);
}

.bookshelf-page__filter-bar {
  display: flex;
  gap: 18px;
  align-items: center;
  min-width: 0;
}

.bookshelf-page__tabs-wrap {
  flex: 1 1 auto;
  min-width: 0;
  display: flex;
  align-items: center;
}

.bookshelf-page__tabs {
  flex: 1 1 auto;
  min-width: 0;
  display: flex;
  gap: 10px;
  align-items: center;
  overflow-x: auto;
  overflow-y: hidden;
  padding: 4px;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.bookshelf-page__tabs::-webkit-scrollbar {
  display: none;
}

.bookshelf-page__tab {
  flex: 0 0 auto;
  min-height: 38px;
  padding: 0 16px;
  border: 1px solid transparent;
  border-radius: 999px;
  background: transparent;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 600;
  line-height: 1;
  white-space: nowrap;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition:
    background-color 180ms ease,
    border-color 180ms ease,
    color 180ms ease,
    box-shadow 180ms ease;
}

.bookshelf-page__tab:hover {
  color: var(--text-primary);
  background: rgba(109, 90, 74, 0.08);
}

.bookshelf-page__tab--active {
  color: var(--primary-color);
  background: rgba(184, 93, 54, 0.12);
  border-color: rgba(184, 93, 54, 0.18);
  box-shadow: inset 0 0 0 1px rgba(184, 93, 54, 0.06);
}

.bookshelf-page__filter-actions {
  flex: 0 0 auto;
  min-width: clamp(340px, 34vw, 520px);
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  align-items: center;
}

.bookshelf-page__sort {
  width: 138px;
  flex: 0 0 auto;
}

.bookshelf-page__search {
  width: 100%;
  min-width: 0;
  display: flex;
  gap: 10px;
  align-items: center;
}

.bookshelf-page__search :deep(.n-input) {
  flex: 1 1 auto;
  min-width: 0;
}

.bookshelf-page__search :deep(.n-button) {
  flex: 0 0 auto;
  min-width: 72px;
  height: 34px;
  white-space: nowrap;
}

.bookshelf-page__alert {
  border-radius: 14px;
}

.bookshelf-page__empty {
  padding: 52px 24px;
  border: 1px solid rgba(109, 90, 74, 0.1);
  border-radius: 22px;
  background: rgba(255, 250, 242, 0.78);
}

.bookshelf-page__empty-tip {
  color: var(--text-secondary);
  font-size: 14px;
}

.bookshelf-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
  align-items: stretch;
}

.bookshelf-list--loading {
  align-items: stretch;
}

.bookshelf-item {
  min-width: 0;
  height: 100%;
  display: grid;
  grid-template-columns: 68px minmax(0, 1fr);
  gap: 16px;
  align-items: start;
  padding: 18px;
  border: 1px solid rgba(109, 90, 74, 0.1);
  border-radius: 20px;
  background: rgba(255, 252, 247, 0.82);
  box-shadow: 0 10px 28px rgba(82, 55, 28, 0.06);
  cursor: pointer;
  transition:
    border-color 180ms ease,
    box-shadow 180ms ease,
    transform 180ms ease;
}

.bookshelf-item:hover {
  transform: translateY(-2px);
  border-color: rgba(184, 93, 54, 0.18);
  box-shadow: 0 18px 34px rgba(82, 55, 28, 0.08);
}

.bookshelf-item--loading {
  min-height: 216px;
}

.bookshelf-item__cover {
  position: relative;
  display: grid;
  justify-items: center;
  align-content: center;
  gap: 4px;
  width: 68px;
  min-height: 94px;
  padding: 10px 8px;
  border: 1px solid rgba(109, 90, 74, 0.12);
  border-radius: 14px;
  background: linear-gradient(180deg, #fffdf8 0%, #f3eadb 100%);
  color: #6d5a4a;
  overflow: hidden;
}

.bookshelf-item__cover--filled {
  padding: 0;
  background: rgba(255, 255, 255, 0.72);
}

.bookshelf-item__cover--loading {
  background: rgba(255, 255, 255, 0.82);
}

.bookshelf-item__cover-image {
  width: 100%;
  height: 100%;
  min-height: 94px;
  object-fit: cover;
  display: block;
}

.bookshelf-item__cover-type {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--primary-color);
}

.bookshelf-item__cover-letter {
  font-family: var(--font-display);
  font-size: 28px;
  line-height: 1;
}

.bookshelf-item__cover-text {
  font-size: 11px;
  color: var(--text-secondary);
}

.bookshelf-item__body {
  min-width: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.bookshelf-item__header-block {
  min-width: 0;
  display: grid;
  gap: 10px;
}

.bookshelf-item__title-row {
  min-width: 0;
  display: flex;
  gap: 8px;
  align-items: start;
}

.bookshelf-item__title {
  flex: 1;
  min-width: 0;
  margin: 0;
  font-size: 18px;
  line-height: 1.45;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}

.bookshelf-item__badge {
  flex-shrink: 0;
  margin-top: 2px;
  padding: 3px 9px;
  border-radius: 999px;
  background: rgba(184, 93, 54, 0.1);
  color: var(--primary-color);
  font-size: 12px;
  font-weight: 600;
}

.bookshelf-item__status-row,
.bookshelf-item__facts,
.bookshelf-item__progress-head span {
  color: var(--text-secondary);
}

.bookshelf-item__status-row {
  display: flex;
  gap: 8px 12px;
  flex-wrap: wrap;
  min-width: 0;
  font-size: 12px;
}

.bookshelf-item__facts {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px 12px;
  font-size: 13px;
}

.bookshelf-item__facts span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bookshelf-item__groups {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.bookshelf-item__footer {
  margin-top: auto;
  display: grid;
  gap: 12px;
}

.bookshelf-item__progress {
  display: grid;
  gap: 8px;
}

.bookshelf-item__progress-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: baseline;
  font-size: 12px;
}

.bookshelf-item__progress-head strong {
  color: var(--text-primary);
  font-size: 13px;
}

.bookshelf-item__actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.bookshelf-item__action {
  min-width: 0;
}

.bookshelf-item__action--primary {
  font-weight: 600;
}

@media (max-width: 1240px) {
  .bookshelf-list {
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  }

  .bookshelf-page__filter-actions {
    min-width: 320px;
  }
}

@media (max-width: 980px) {
  .bookshelf-page {
    gap: 18px;
  }

  .bookshelf-page__header {
    flex-direction: column;
    align-items: stretch;
  }

  .bookshelf-page__filter-bar {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .bookshelf-page__filter-actions {
    min-width: 0;
    flex-wrap: wrap;
  }

  .bookshelf-page__sort {
    width: 100%;
  }

  .bookshelf-page__search {
    width: 100%;
  }

  .bookshelf-list {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 16px;
  }

  .bookshelf-item {
    padding: 16px;
  }
}

@media (max-width: 720px) {
  .bookshelf-page {
    gap: 16px;
  }

  .bookshelf-list {
    grid-template-columns: 1fr;
  }

  .bookshelf-item {
    grid-template-columns: 62px minmax(0, 1fr);
    gap: 14px;
    padding: 14px;
  }

  .bookshelf-item__cover,
  .bookshelf-item__cover-image {
    width: 62px;
    min-height: 88px;
  }

  .bookshelf-item__title {
    font-size: 17px;
    -webkit-line-clamp: 3;
  }

  .bookshelf-item__facts {
    grid-template-columns: 1fr;
  }

  .bookshelf-page__tabs {
    gap: 8px;
  }

  .bookshelf-page__tab {
    min-height: 36px;
    padding: 0 14px;
  }

  .bookshelf-page__filter-actions {
    display: grid;
    gap: 10px;
  }
}
</style>
