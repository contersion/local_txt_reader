<template>
  <div class="book-detail-page">
    <section class="book-detail-page__topbar">
      <n-button tertiary @click="goBack">返回书架</n-button>
      <span class="book-detail-page__crumb">{{ detail?.source_kind === "online" ? "Online Book" : "Local Book" }}</span>
    </section>

    <section v-if="loading" class="book-detail-page__loading">
      <n-card :bordered="false" class="book-detail-page__loading-card">
        <n-skeleton text :repeat="4" />
        <n-skeleton style="margin-top: 18px;" text :repeat="3" />
      </n-card>
      <n-card :bordered="false" class="book-detail-page__loading-card">
        <n-skeleton text :repeat="8" />
      </n-card>
    </section>

    <page-status-panel
      v-else-if="pageError"
      variant="error"
      title="书籍详情暂时无法加载"
      :description="pageError"
    >
      <template #action>
        <n-button type="primary" @click="reloadPage">重新加载</n-button>
      </template>
    </page-status-panel>

    <template v-else-if="detail">
      <section class="detail-hero">
        <div class="detail-hero__cover" :class="{ 'detail-hero__cover--filled': !!detail.cover_url }">
          <img
            v-if="resolvedCoverUrl"
            class="detail-hero__cover-image"
            :src="resolvedCoverUrl"
            :alt="`${detail.title} 封面`"
          />
          <template v-else>
            <div class="detail-hero__cover-badge">{{ detail.source_kind === "online" ? "ONLINE" : "TXT" }}</div>
            <div class="detail-hero__cover-letter">{{ getCoverLetter(detail.title) }}</div>
          </template>
        </div>

        <div class="detail-hero__body">
          <div class="detail-hero__eyebrow">{{ detail.source_label }}</div>
          <h1 class="detail-hero__title">{{ detail.title }}</h1>
          <p class="detail-hero__author">{{ detail.author || "作者未填写" }}</p>
          <p class="detail-hero__description">
            {{
              detail.description ||
              (isLocal
                ? "这本书还没有补充简介，你可以先查看目录、继续阅读，或切换目录规则后重新解析。"
                : "这本在线书籍还没有补充简介，你可以先查看目录或直接进入阅读。")
            }}
          </p>

          <div class="detail-hero__tags">
            <n-tag round :bordered="false">总章节 {{ formatNumber(detail.total_chapters) }}</n-tag>
            <n-tag round :bordered="false">{{ detail.source_label }}</n-tag>
            <n-tag v-if="isLocal" round :bordered="false">总字数 {{ formatWordCount(detail.total_words) }}</n-tag>
            <n-tag round :bordered="false">{{ progressTagLabel }}</n-tag>
            <n-tag round :bordered="false">{{ progressPercentLabel }}</n-tag>
          </div>

          <div class="detail-hero__actions">
            <n-button type="primary" size="large" :loading="readingPending" @click="handleReadAction">
              {{ readActionLabel }}
            </n-button>
            <n-button tertiary size="large" @click="openCatalog">
              查看目录
            </n-button>
            <n-button
              v-if="actions.canEditMetadata"
              secondary
              size="large"
              @click="openEditor"
            >
              编辑信息
            </n-button>
          </div>
        </div>
      </section>

      <section class="detail-grid">
        <n-card :bordered="false" class="detail-card">
          <template #header>
            <span class="detail-card__heading">阅读信息</span>
          </template>

          <div class="detail-info-grid">
            <div class="detail-info-item">
              <span>作者</span>
              <strong>{{ detail.author || "未填写" }}</strong>
            </div>
            <div class="detail-info-item">
              <span>阅读进度</span>
              <strong>{{ progressPercentLabel }}</strong>
            </div>
            <div class="detail-info-item">
              <span>最近阅读</span>
              <strong>{{ formatOptionalDate(detail.recent_read_at) }}</strong>
            </div>
            <div class="detail-info-item">
              <span>阅读定位</span>
              <strong>{{ progressTagLabel }}</strong>
            </div>
            <div class="detail-info-item detail-info-item--wide">
              <span>简介</span>
              <strong class="detail-info-item__multiline">
                {{ detail.description || "暂无简介" }}
              </strong>
            </div>
          </div>

          <div v-if="detail.groups.length > 0" class="detail-group-list">
            <span class="detail-group-list__label">分组</span>
            <div class="detail-group-list__tags">
              <n-tag
                v-for="group in detail.groups"
                :key="group.id"
                round
                :bordered="false"
                type="warning"
              >
                {{ group.name }}
              </n-tag>
            </div>
          </div>
        </n-card>

        <n-card v-if="isLocal && detail.local_file" :bordered="false" class="detail-card">
          <template #header>
            <span class="detail-card__heading">文件信息</span>
          </template>

          <div class="detail-info-grid">
            <div class="detail-info-item">
              <span>文件名</span>
              <strong>{{ detail.local_file.file_name }}</strong>
            </div>
            <div class="detail-info-item">
              <span>编码</span>
              <strong>{{ detail.local_file.encoding }}</strong>
            </div>
            <div class="detail-info-item">
              <span>收录时间</span>
              <strong>{{ formatDate(detail.created_at) }}</strong>
            </div>
            <div class="detail-info-item">
              <span>更新时间</span>
              <strong>{{ formatDate(detail.updated_at) }}</strong>
            </div>
          </div>

          <div class="detail-file-path">
            <span class="detail-file-path__label">本地文件</span>
            <code>{{ detail.local_file.file_path }}</code>
          </div>
        </n-card>

        <n-card v-else-if="detail.online_meta" :bordered="false" class="detail-card">
          <template #header>
            <span class="detail-card__heading">在线来源</span>
          </template>

          <div class="detail-info-grid">
            <div class="detail-info-item">
              <span>书源</span>
              <strong>{{ detail.online_meta.source_name }}</strong>
            </div>
            <div class="detail-info-item">
              <span>远端 ID</span>
              <strong>{{ detail.online_meta.remote_book_id || "未提供" }}</strong>
            </div>
            <div class="detail-info-item">
              <span>目录同步时间</span>
              <strong>{{ formatOptionalDate(detail.online_meta.latest_catalog_fetched_at) }}</strong>
            </div>
            <div class="detail-info-item">
              <span>详情链接</span>
              <strong class="detail-info-item__multiline">{{ detail.online_meta.detail_url }}</strong>
            </div>
          </div>
        </n-card>

        <n-card v-if="isLocal" :bordered="false" class="detail-card detail-card--full">
          <template #header>
            <span class="detail-card__heading">目录规则</span>
          </template>

          <div class="detail-rule-card">
            <div class="detail-rule-card__current">
              <span>当前使用</span>
              <strong>{{ currentRuleName }}</strong>
              <p>{{ currentRuleDescription }}</p>
            </div>

            <n-alert v-if="rulesError" type="warning" :show-icon="false" class="detail-rule-card__alert">
              {{ rulesError }}
            </n-alert>

            <div class="detail-rule-card__actions">
              <n-select
                v-model:value="selectedRuleId"
                :options="ruleOptions"
                :disabled="reparsePending || ruleOptions.length === 0"
                placeholder="选择目录规则"
              />
              <n-button
                secondary
                :loading="reparsePending"
                :disabled="!selectedRuleId"
                @click="handleReparse"
              >
                重新解析目录
              </n-button>
            </div>
          </div>
        </n-card>
      </section>

      <n-modal
        v-if="isLocal"
        v-model:show="editorVisible"
        preset="card"
        class="metadata-modal"
        title="编辑书籍信息"
        :bordered="false"
      >
        <div class="metadata-modal__layout">
          <div class="metadata-modal__cover-panel">
            <div class="metadata-modal__cover" :class="{ 'metadata-modal__cover--filled': !!detail.cover_url }">
              <img
                v-if="resolvedCoverUrl"
                class="metadata-modal__cover-image"
                :src="resolvedCoverUrl"
                :alt="`${detail.title} 封面`"
              />
              <template v-else>
                <span class="metadata-modal__cover-type">TXT</span>
                <strong class="metadata-modal__cover-letter">{{ getCoverLetter(detail.title) }}</strong>
                <span class="metadata-modal__cover-text">无封面</span>
              </template>
            </div>

            <div class="metadata-modal__cover-actions">
              <n-upload
                accept="image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp"
                :show-file-list="false"
                :max="1"
                :custom-request="handleCoverUpload"
              >
                <n-button secondary :loading="coverUploading">上传封面</n-button>
              </n-upload>
              <n-button
                v-if="detail.cover_url"
                quaternary
                type="error"
                :loading="coverDeleting"
                @click="handleRemoveCover"
              >
                删除封面
              </n-button>
            </div>
          </div>

          <div class="metadata-modal__form">
            <label class="metadata-modal__field">
              <span>书名</span>
              <n-input v-model:value="editableTitle" placeholder="用于全局显示的书名" clearable />
            </label>

            <label class="metadata-modal__field">
              <span>作者</span>
              <n-input v-model:value="editableAuthor" placeholder="作者可留空" clearable />
            </label>

            <label class="metadata-modal__field">
              <span>简介</span>
              <n-input
                v-model:value="editableDescription"
                type="textarea"
                placeholder="支持多行简介"
                :autosize="{ minRows: 6, maxRows: 12 }"
              />
            </label>
          </div>
        </div>

        <template #action>
          <div class="metadata-modal__footer">
            <n-button @click="editorVisible = false">取消</n-button>
            <n-button type="primary" :loading="metadataSaving" @click="handleSaveMetadata">
              保存修改
            </n-button>
          </div>
        </template>
      </n-modal>

      <chapter-catalog-modal-drawer
        v-model:show="catalogVisible"
        :book-title="detail.title"
        :chapter-count="detail.total_chapters || 0"
        :chapters="catalog"
        @select="handleCatalogSelect"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import {
  NAlert,
  NButton,
  NCard,
  NInput,
  NModal,
  NSelect,
  NSkeleton,
  NTag,
  NUpload,
  useMessage,
  type UploadCustomRequestOptions,
} from "naive-ui";
import { useRouter } from "vue-router";

import { booksApi } from "../api/books";
import { getErrorMessage } from "../api/client";
import { chapterRulesApi } from "../api/chapter-rules";
import ChapterCatalogModalDrawer from "../components/ChapterCatalogModalDrawer.vue";
import { useBookDetailSource } from "../composables/useBookDetailSource";
import PageStatusPanel from "../components/PageStatusPanel.vue";
import type { BookChapter, ChapterRule, LibraryBookDetail, ReadingProgress } from "../types/api";
import { formatDateTime, formatNumber, formatPercent, formatWordCount } from "../utils/format";

const props = defineProps<{
  libraryBookId: string;
}>();

const router = useRouter();
const message = useMessage();
const BOOK_METADATA_UPDATED_EVENT = "books:metadata-updated";
const detail = ref<LibraryBookDetail | null>(null);
const catalog = ref<BookChapter[]>([]);
const progress = ref<ReadingProgress | null>(null);
const rules = ref<ChapterRule[]>([]);
const selectedRuleId = ref<number | null>(null);
const loading = ref(true);
const pageError = ref<string | null>(null);
const rulesError = ref<string | null>(null);
const readingPending = ref(false);
const reparsePending = ref(false);
const editorVisible = ref(false);
const metadataSaving = ref(false);
const coverUploading = ref(false);
const coverDeleting = ref(false);
const catalogVisible = ref(false);
const editableTitle = ref("");
const editableAuthor = ref("");
const editableDescription = ref("");

const isLocal = computed(() => detail.value?.source_kind === "local");
const actions = computed(() => ({
  canEditMetadata: detail.value?.source_kind === "local",
  canUploadCover: detail.value?.source_kind === "local",
  canReparseCatalog: detail.value?.source_kind === "local",
}));

const ruleOptions = computed(() => {
  return rules.value.map((rule) => ({
    label: rule.is_builtin ? `${rule.rule_name}（内置）` : rule.rule_name,
    value: rule.id,
  }));
});

const currentRuleName = computed(() => {
  if (!detail.value?.chapter_rule?.rule_name) {
    const selectedRule = rules.value.find((rule) => rule.id === selectedRuleId.value);
    return selectedRule?.rule_name || "未指定";
  }

  return detail.value.chapter_rule.rule_name;
});

const currentRuleDescription = computed(() => {
  if (!detail.value?.chapter_rule?.description) {
    const selectedRule = rules.value.find((rule) => rule.id === selectedRuleId.value);
    return selectedRule?.description || "你可以在这里切换规则，并重新解析当前书籍的目录。";
  }

  return detail.value.chapter_rule.description;
});

const readActionLabel = computed(() => {
  return progress.value ? "继续阅读" : "开始阅读";
});

const progressTagLabel = computed(() => {
  if (!progress.value) {
    return "尚未开始";
  }

  return `上次读到第 ${formatNumber(progress.value.chapter_index + 1)} 章`;
});

const progressPercentLabel = computed(() => {
  return `进度 ${formatPercent(detail.value?.progress_percent ?? progress.value?.percent ?? 0)}`;
});

const resolvedCoverUrl = computed(() => detail.value?.cover_url || null);

function formatDate(value: string) {
  return formatDateTime(value, "时间未知");
}

function formatOptionalDate(value: string | null | undefined) {
  return formatDateTime(value, "未开始");
}

function getCoverLetter(title: string) {
  const normalized = title.trim();
  return normalized ? normalized.slice(0, 1).toUpperCase() : "T";
}

function syncEditorFields(bookDetail: LibraryBookDetail) {
  editableTitle.value = bookDetail.title;
  editableAuthor.value = bookDetail.author || "";
  editableDescription.value = bookDetail.description || "";
}

async function loadRules() {
  if (!isLocal.value) {
    rules.value = [];
    rulesError.value = null;
    selectedRuleId.value = null;
    return;
  }

  rulesError.value = null;
  try {
    rules.value = await chapterRulesApi.list();
    if (!selectedRuleId.value) {
      selectedRuleId.value =
        detail.value?.chapter_rule?.id ??
        rules.value.find((rule) => rule.is_default)?.id ??
        rules.value[0]?.id ??
        null;
    }
  } catch (error) {
    rules.value = [];
    rulesError.value = getErrorMessage(error);
  }
}

async function loadPage() {
  loading.value = true;
  pageError.value = null;

  try {
    const payload = await useBookDetailSource(props.libraryBookId).load();
    detail.value = payload.detail;
    catalog.value = payload.catalog;
    progress.value = payload.progress;
    syncEditorFields(payload.detail);
    await loadRules();
  } catch (error) {
    detail.value = null;
    catalog.value = [];
    progress.value = null;
    pageError.value = getErrorMessage(error);
  } finally {
    loading.value = false;
  }
}

function reloadPage() {
  void loadPage();
}

function goBack() {
  void router.push({ name: "books" });
}

function goToChapter(chapterIndex: number) {
  void router.push({
    name: "reader",
    params: {
      libraryBookId: props.libraryBookId,
      chapterIndex,
    },
  });
}

function openCatalog() {
  catalogVisible.value = true;
}

function openEditor() {
  if (!detail.value || !actions.value.canEditMetadata) {
    return;
  }

  syncEditorFields(detail.value);
  editorVisible.value = true;
}

function handleCatalogSelect(chapterIndex: number) {
  catalogVisible.value = false;
  goToChapter(chapterIndex);
}

async function handleReadAction() {
  readingPending.value = true;

  try {
    if (!progress.value) {
      goToChapter(0);
      return;
    }

    goToChapter(progress.value.chapter_index);
  } finally {
    readingPending.value = false;
  }
}

async function handleSaveMetadata() {
  if (!detail.value || !isLocal.value) {
    return;
  }

  metadataSaving.value = true;

  try {
    await booksApi.updateMetadata(detail.value.entity_id, {
      title: editableTitle.value.trim() || null,
      author: editableAuthor.value.trim() || null,
      description: editableDescription.value.trim() || null,
    });
    await loadPage();
    if (typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent(BOOK_METADATA_UPDATED_EVENT, { detail: { libraryBookId: props.libraryBookId } }));
    }
    editorVisible.value = false;
    message.success("书籍信息已保存");
  } catch (error) {
    message.error(getErrorMessage(error));
  } finally {
    metadataSaving.value = false;
  }
}

async function handleCoverUpload(options: UploadCustomRequestOptions) {
  if (!detail.value || !isLocal.value) {
    options.onError?.();
    return;
  }

  const file = options.file.file;
  if (!(file instanceof File)) {
    options.onError?.();
    message.error("未找到可上传的封面文件");
    return;
  }

  coverUploading.value = true;

  try {
    await booksApi.uploadCover(detail.value.entity_id, file);
    await loadPage();
    options.onFinish?.();
    message.success("封面已更新");
  } catch (error) {
    options.onError?.();
    message.error(getErrorMessage(error));
  } finally {
    coverUploading.value = false;
  }
}

async function handleRemoveCover() {
  if (!detail.value || !isLocal.value) {
    return;
  }

  coverDeleting.value = true;

  try {
    await booksApi.deleteCover(detail.value.entity_id);
    await loadPage();
    message.success("封面已删除");
  } catch (error) {
    message.error(getErrorMessage(error));
  } finally {
    coverDeleting.value = false;
  }
}

async function handleReparse() {
  if (!detail.value || !isLocal.value) {
    return;
  }

  if (!selectedRuleId.value) {
    message.warning("请先选择一个目录规则");
    return;
  }

  reparsePending.value = true;

  try {
    await booksApi.reparse(detail.value.entity_id, selectedRuleId.value);
    message.success("目录已重新解析");
    await loadPage();
  } catch (error) {
    message.error(getErrorMessage(error));
  } finally {
    reparsePending.value = false;
  }
}

watch(
  () => props.libraryBookId,
  () => {
    catalogVisible.value = false;
    editorVisible.value = false;
    void loadPage();
  },
  { immediate: true },
);
</script>

<style scoped>
.book-detail-page {
  display: grid;
  gap: 24px;
}

.book-detail-page__topbar {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
}

.book-detail-page__crumb {
  color: var(--text-secondary);
  font-size: 13px;
}

.book-detail-page__loading {
  display: grid;
  gap: 18px;
}

.book-detail-page__loading-card {
  min-height: 220px;
}

.detail-hero {
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr);
  gap: 24px;
  padding: clamp(24px, 4vw, 32px);
  border-radius: 28px;
  background:
    radial-gradient(circle at top right, rgba(52, 107, 97, 0.18), transparent 26%),
    radial-gradient(circle at bottom left, rgba(184, 93, 54, 0.14), transparent 32%),
    color-mix(in srgb, var(--surface-color) 92%, white 8%);
  box-shadow: var(--surface-shadow);
}

.detail-hero__cover {
  position: relative;
  display: grid;
  place-items: center;
  min-height: 280px;
  border-radius: 24px;
  background:
    linear-gradient(155deg, rgba(184, 93, 54, 0.92), rgba(52, 107, 97, 0.92)),
    linear-gradient(180deg, rgba(255, 255, 255, 0.16), transparent);
  color: white;
  overflow: hidden;
}

.detail-hero__cover--filled {
  background: rgba(255, 255, 255, 0.7);
}

.detail-hero__cover-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.detail-hero__cover-badge {
  position: absolute;
  top: 16px;
  left: 16px;
  z-index: 1;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.2);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.detail-hero__cover-letter {
  position: relative;
  z-index: 1;
  font-family: var(--font-display);
  font-size: 72px;
  font-weight: 700;
}

.detail-hero__body {
  display: grid;
  gap: 18px;
  align-content: center;
}

.detail-hero__eyebrow {
  display: inline-flex;
  width: fit-content;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(52, 107, 97, 0.12);
  color: var(--accent-color);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.detail-hero__title {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(30px, 4vw, 46px);
  line-height: 1.08;
}

.detail-hero__author {
  margin: 0;
  color: var(--text-secondary);
  font-size: 18px;
}

.detail-hero__description {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.8;
  white-space: pre-wrap;
}

.detail-hero__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.detail-hero__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}

.detail-card__heading {
  font-weight: 700;
}

.detail-card--full {
  grid-column: 1 / -1;
}

.detail-info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.detail-info-item {
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.55);
}

.detail-info-item--wide {
  grid-column: 1 / -1;
}

.detail-info-item span {
  display: block;
  color: var(--text-secondary);
  font-size: 12px;
}

.detail-info-item strong {
  display: block;
  margin-top: 6px;
  line-height: 1.6;
}

.detail-info-item__multiline {
  white-space: pre-wrap;
  word-break: break-word;
}

.detail-group-list {
  margin-top: 14px;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.55);
}

.detail-group-list__label,
.detail-file-path__label {
  display: block;
  margin-bottom: 8px;
  color: var(--text-secondary);
  font-size: 12px;
}

.detail-group-list__tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.detail-file-path {
  margin-top: 14px;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.55);
}

.detail-file-path code {
  white-space: pre-wrap;
  word-break: break-all;
  color: var(--text-primary);
}

.detail-rule-card {
  display: grid;
  gap: 16px;
}

.detail-rule-card__current span {
  display: block;
  color: var(--text-secondary);
  font-size: 12px;
}

.detail-rule-card__current strong {
  display: block;
  margin-top: 6px;
  font-size: 18px;
}

.detail-rule-card__current p {
  margin: 10px 0 0;
  color: var(--text-secondary);
  line-height: 1.8;
}

.detail-rule-card__alert {
  border-radius: 16px;
}

.detail-rule-card__actions {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
}

.metadata-modal :deep(.n-card) {
  width: min(920px, calc(100vw - 24px));
  border-radius: 24px;
}

.metadata-modal__layout {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr);
  gap: 20px;
}

.metadata-modal__cover-panel {
  display: grid;
  gap: 14px;
}

.metadata-modal__cover {
  display: grid;
  place-items: center;
  min-height: 280px;
  border-radius: 22px;
  border: 1px solid rgba(109, 90, 74, 0.12);
  background: linear-gradient(180deg, #fffdf8 0%, #f3eadb 100%);
  overflow: hidden;
  color: #6d5a4a;
}

.metadata-modal__cover--filled {
  background: rgba(255, 255, 255, 0.72);
}

.metadata-modal__cover-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.metadata-modal__cover-type {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--primary-color);
}

.metadata-modal__cover-letter {
  font-family: var(--font-display);
  font-size: 68px;
  line-height: 1;
}

.metadata-modal__cover-text {
  font-size: 12px;
  color: var(--text-secondary);
}

.metadata-modal__cover-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.metadata-modal__form {
  display: grid;
  gap: 16px;
}

.metadata-modal__field {
  display: grid;
  gap: 8px;
}

.metadata-modal__field span {
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 600;
}

.metadata-modal__footer {
  width: 100%;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

@media (max-width: 960px) {
  .detail-hero,
  .detail-grid,
  .metadata-modal__layout {
    grid-template-columns: 1fr;
  }

  .detail-hero__cover {
    min-height: 220px;
  }
}

@media (max-width: 720px) {
  .book-detail-page__topbar,
  .detail-hero__actions,
  .detail-rule-card__actions,
  .detail-info-grid,
  .metadata-modal__footer {
    display: grid;
    grid-template-columns: 1fr;
  }

  .detail-info-item--wide {
    grid-column: auto;
  }
}
</style>
