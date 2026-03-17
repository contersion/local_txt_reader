<template>
  <div
    class="reader-page"
    :class="[
      `reader-page--${preferences.theme}`,
      { 'reader-page--compact': isCompactViewport },
    ]"
    :style="readerStyleVars"
  >
    <div v-if="loading" class="reader-loading">
      <section class="reader-glass reader-loading__panel reader-loading__panel--rail">
        <n-skeleton text :repeat="3" />
        <n-skeleton style="margin-top: 18px;" text :repeat="4" />
      </section>
      <section class="reader-loading__main">
        <section class="reader-glass reader-loading__panel">
          <n-skeleton text :repeat="3" />
          <n-skeleton style="margin-top: 14px;" text :repeat="2" />
        </section>
        <section class="reader-paper reader-loading__paper">
          <n-skeleton text :repeat="14" />
        </section>
      </section>
      <section class="reader-glass reader-loading__panel reader-loading__panel--float">
        <n-skeleton text :repeat="4" />
      </section>
    </div>

    <page-status-panel
      v-else-if="pageError"
      variant="error"
      title="阅读页暂时无法打开"
      :description="pageError"
    >
      <template #action>
        <n-button type="primary" @click="loadReader">重新加载</n-button>
        <n-button tertiary @click="goBack">返回详情</n-button>
      </template>
    </page-status-panel>

    <page-status-panel
      v-else-if="chapters.length === 0"
      title="这本书暂时没有可展示的目录"
      description="可以先回到书籍详情页重新解析目录，或稍后再刷新一次。"
    >
      <template #action>
        <n-button secondary @click="loadReader">重新加载</n-button>
        <n-button tertiary @click="goBack">返回详情</n-button>
      </template>
    </page-status-panel>

    <div v-else class="reader-shell">
      <aside class="reader-rail" :class="{ 'reader-rail--active': shouldShowChrome }">
        <div class="reader-glass reader-rail__panel" @click.stop>
          <div class="reader-rail__brand">
            <span class="reader-eyebrow">Immersive Reader</span>
            <strong class="reader-rail__chapter">{{ currentChapterPositionLabel }}</strong>
            <span class="reader-rail__sync">{{ syncStatusTagLabel }}</span>
          </div>

          <div class="reader-rail__actions">
            <button type="button" class="reader-rail__action" @click.stop="goBack">
              <strong>返回详情</strong>
              <span>回到书籍信息与目录入口</span>
            </button>
            <button type="button" class="reader-rail__action" @click.stop="openDrawer('catalog')">
              <strong>目录</strong>
              <span>从左侧抽屉浏览章节</span>
            </button>
            <button type="button" class="reader-rail__action" @click.stop="openDrawer('settings')">
              <strong>设置</strong>
              <span>字体、行高与主题</span>
            </button>
          </div>
        </div>
      </aside>

      <main class="reader-stage" @click="handleReadingSurfaceTap">
        <section class="reader-stage__hero">
          <span class="reader-eyebrow">Scroll Reading</span>

          <div class="reader-stage__header">
            <div>
              <p v-if="bookTitle" class="reader-stage__book">{{ bookTitle }}</p>
              <p class="reader-stage__chapter">{{ currentChapterPositionLabel }}</p>
              <h1 class="reader-stage__title">{{ currentChapterTitle }}</h1>
            </div>

            <div class="reader-stage__stat">
              <span>当前进度</span>
              <strong>{{ progressPercentLabel }}</strong>
              <small>{{ syncStatusTagLabel }}</small>
            </div>
          </div>

        </section>

        <section class="reader-paper">
          <n-alert
            v-if="chapterError"
            type="error"
            :show-icon="false"
            class="reader-page__alert"
          >
            {{ chapterError }}
          </n-alert>

          <div v-if="!currentChapter && chapterLoading" class="reader-content reader-content--loading">
            <n-skeleton text :repeat="10" />
          </div>

          <article
            v-else
            ref="contentRef"
            class="reader-content"
            :class="{ 'reader-content--dimmed': chapterLoading }"
          >
            <template v-if="currentChapter">
              <p
                v-for="(paragraph, index) in currentChapterParagraphs"
                :key="`paragraph-${currentChapterIndex}-${index}`"
                class="reader-content__paragraph"
              >
                {{ paragraph }}
              </p>
            </template>
            <template v-else>正文载入中...</template>
          </article>
          <section v-if="isCompactViewport" class="reader-paper__chapter-nav" @click.stop>
            <div class="reader-paper__chapter-actions">
              <n-button
                block
                size="large"
                :disabled="!canGoPrev || chapterLoading"
                @click="handlePrevChapter"
              >
                上一章
              </n-button>
              <n-button
                block
                type="primary"
                size="large"
                :disabled="!canGoNext || chapterLoading"
                @click="handleNextChapter"
              >
                下一章
              </n-button>
            </div>
          </section>
        </section>
      </main>

      <aside class="reader-float">
        <div class="reader-glass reader-float__panel" @click.stop>
          <div class="reader-float__stat">
            <span>已读进度</span>
            <strong>{{ progressPercentLabel }}</strong>
          </div>

          <n-progress
            type="line"
            :percentage="currentProgressPercent"
            :show-indicator="false"
            color="var(--reader-accent)"
            rail-color="var(--reader-progress-rail)"
          />

          <div class="reader-float__summary">
            <span>{{ currentChapterPositionLabel }}</span>
            <span>{{ syncStatusTagLabel }}</span>
            <span>{{ syncedProgressLabel }}</span>
          </div>

          <div class="reader-float__actions">
            <n-button secondary :disabled="!canGoPrev || chapterLoading" @click="handlePrevChapter">
              上一章
            </n-button>
            <n-button type="primary" :disabled="!canGoNext || chapterLoading" @click="handleNextChapter">
              下一章
            </n-button>
          </div>
        </div>
      </aside>
    </div>

    <n-drawer v-model:show="isDrawerOpen" placement="left" :width="drawerWidth">
      <n-drawer-content :title="drawerTitle" closable body-content-style="padding: 20px;">
        <template v-if="activeDrawer === 'catalog'">
          <div class="reader-drawer__summary">
            <div>
              <span>{{ currentChapterPositionLabel }}</span>
              <strong>{{ progressPercentLabel }}</strong>
            </div>
            <p>{{ syncedProgressLabel }}</p>
          </div>

          <n-progress
            type="line"
            :percentage="currentProgressPercent"
            :show-indicator="false"
            color="var(--reader-accent)"
            rail-color="var(--reader-progress-rail)"
            class="reader-drawer__progress"
          />

          <div class="reader-catalog__list reader-catalog__list--drawer">
            <button
              v-for="chapter in chapters"
              :key="`drawer-${chapter.id}`"
              type="button"
              class="reader-catalog__item"
              :class="{
                'reader-catalog__item--active': chapter.chapter_index === currentChapterIndex,
              }"
              @click="handleChapterSelect(chapter.chapter_index)"
            >
              <span class="reader-catalog__index">{{ formatChapterOrdinal(chapter.chapter_index) }}</span>
              <strong class="reader-catalog__title">{{ chapter.chapter_title }}</strong>
            </button>
          </div>
        </template>

        <template v-else>
          <div class="reader-settings">
            <section class="reader-settings__group">
              <div class="reader-settings__label-row">
                <span>字体大小</span>
                <strong>{{ preferences.fontSize }}px</strong>
              </div>
              <n-slider v-model:value="preferences.fontSize" :step="1" :min="15" :max="28" />
            </section>

            <section class="reader-settings__group">
              <div class="reader-settings__label-row">
                <span>行高</span>
                <strong>{{ preferences.lineHeight.toFixed(2) }}</strong>
              </div>
              <n-slider v-model:value="preferences.lineHeight" :step="0.05" :min="1.45" :max="2.5" />
            </section>

            <section class="reader-settings__group">
              <div class="reader-settings__label-row">
                <span>阅读主题</span>
                <strong>{{ preferences.theme === 'dark' ? '深色' : '浅色' }}</strong>
              </div>
              <n-radio-group v-model:value="preferences.theme" name="reader-theme">
                <n-space>
                  <n-radio-button value="light">浅色</n-radio-button>
                  <n-radio-button value="dark">深色</n-radio-button>
                </n-space>
              </n-radio-group>
            </section>

            <section class="reader-settings__group">
              <div class="reader-settings__label-row">
                <span>字间距</span>
                <strong>{{ preferences.letterSpacing.toFixed(2) }}px</strong>
              </div>
              <n-slider v-model:value="preferences.letterSpacing" :step="0.05" :min="0" :max="2" />
            </section>

            <section class="reader-settings__group">
              <div class="reader-settings__label-row">
                <span>段间距</span>
                <strong>{{ preferences.paragraphSpacing.toFixed(2) }}x</strong>
              </div>
              <n-slider v-model:value="preferences.paragraphSpacing" :step="0.05" :min="0" :max="2.5" />
            </section>

            <section class="reader-settings__group">
              <div class="reader-settings__label-row">
                <span>阅读宽度</span>
                <strong>{{ preferences.contentWidth }}ch</strong>
              </div>
              <n-slider v-model:value="preferences.contentWidth" :step="1" :min="56" :max="96" />
            </section>
          </div>
        </template>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>
<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, reactive, ref, watch } from "vue";
import {
  NAlert,
  NButton,
  NDrawer,
  NDrawerContent,
  NProgress,
  NRadioButton,
  NRadioGroup,
  NSkeleton,
  NSlider,
  NSpace,
} from "naive-ui";
import { useRoute, useRouter } from "vue-router";

import { booksApi } from "../api/books";
import { ApiError, buildApiUrl, getErrorMessage } from "../api/client";
import { usePreferencesStore } from "../stores/preferences";
import type {
  BookChapter,
  BookChapterContent,
  ReadingProgress,
  ReadingProgressPayload,
} from "../types/api";
import PageStatusPanel from "../components/PageStatusPanel.vue";
import { formatPercent } from "../utils/format";
import { authTokenStorage } from "../utils/token";

const PROGRESS_THROTTLE_MS = 15000;
const READER_SCROLL_ANCHOR = 120;
const COMPACT_BREAKPOINT = 980;
const MOBILE_CONTENT_WIDTH_MIN_PERCENT = 84;
const MOBILE_CONTENT_WIDTH_MAX_PERCENT = 100;

type ProgressSnapshot = ReadingProgressPayload;
type ReaderDrawerView = "catalog" | "settings";

interface RouteChapterState {
  provided: boolean;
  valid: boolean;
  value: number;
}

interface ReaderChapterContentView {
  body: string;
  trimmedPrefixLength: number;
}

const props = withDefaults(
  defineProps<{
    bookId: number;
    chapterIndex?: number;
  }>(),
  {
    chapterIndex: 0,
  },
);

const route = useRoute();
const router = useRouter();
const preferencesStore = usePreferencesStore();
const chapters = ref<BookChapter[]>([]);
const bookTitle = ref("");
const progress = ref<ReadingProgress | null>(null);
const sessionProgress = ref<ProgressSnapshot | null>(null);
const currentChapter = ref<BookChapterContent | null>(null);
const currentChapterIndex = ref(0);
const hasMeaningfulReadingActivity = ref(false);
const loading = ref(true);
const chapterLoading = ref(false);
const pageError = ref<string | null>(null);
const chapterError = ref<string | null>(null);
const syncState = ref<"idle" | "pending" | "syncing" | "error">("idle");
const preferences = reactive({
  ...preferencesStore.reader,
});
const contentRef = ref<HTMLElement | null>(null);
const activeDrawer = ref<ReaderDrawerView | null>(null);
const mobileChromeVisible = ref(false);
const viewportWidth = ref(COMPACT_BREAKPOINT + 200);

let progressSaveTimer: ReturnType<typeof setTimeout> | null = null;
let saveInFlight = false;
let queuedSnapshot: ProgressSnapshot | null = null;
let lastSavedProgressKey = "";
let suppressScrollTrackingUntil = 0;

const isCompactViewport = computed(() => viewportWidth.value <= COMPACT_BREAKPOINT);
const shouldShowChrome = computed(() => !isCompactViewport.value || mobileChromeVisible.value);
const progressPercentLabel = computed(() => formatPercent(currentProgressPercent.value));
const drawerTitle = computed(() => (activeDrawer.value === "settings" ? "阅读设置" : "章节目录"));
const drawerWidth = computed(() => Math.min(Math.max(viewportWidth.value - 24, 280), 380));
const isDrawerOpen = computed({
  get: () => activeDrawer.value !== null,
  set: (value: boolean) => {
    if (!value) {
      activeDrawer.value = null;
    }
  },
});
const currentChapterTitle = computed(() => {
  return (
    currentChapter.value?.chapter_title ||
    chapters.value.find((chapter) => chapter.chapter_index === currentChapterIndex.value)?.chapter_title ||
    "正在载入章节"
  );
});
const currentChapterContentView = computed<ReaderChapterContentView>(() => {
  if (!currentChapter.value) {
    return {
      body: "",
      trimmedPrefixLength: 0,
    };
  }

  return buildReaderChapterContentView(
    currentChapter.value.content,
    currentChapter.value.chapter_title || currentChapterTitle.value,
  );
});
const currentChapterBody = computed(() => currentChapterContentView.value.body);
const currentChapterParagraphs = computed(() => buildReaderParagraphs(currentChapterBody.value));
const currentChapterTrimmedPrefixLength = computed(() => currentChapterContentView.value.trimmedPrefixLength);
const currentChapterPositionLabel = computed(() => {
  if (chapters.value.length === 0) {
    return "暂无目录";
  }

  return `第 ${currentChapterIndex.value + 1} / ${chapters.value.length} 章`;
});
const currentProgressPercent = computed(() => {
  if (sessionProgress.value) {
    return sessionProgress.value.percent;
  }

  if (progress.value) {
    return progress.value.percent;
  }

  if (chapters.value.length === 0) {
    return 0;
  }

  return roundPercent(((currentChapterIndex.value + 1) / chapters.value.length) * 100);
});
const syncStatusTagLabel = computed(() => {
  if (syncState.value === "syncing") {
    return "同步中";
  }

  if (syncState.value === "pending") {
    return "待同步";
  }

  if (syncState.value === "error") {
    return "同步待重试";
  }

  return progress.value ? "已同步" : "未同步";
});
const syncedProgressLabel = computed(() => {
  const displayPercent = formatPercent(currentProgressPercent.value);

  if (!progress.value && !sessionProgress.value) {
    return "还没有云端阅读进度";
  }

  if (syncState.value === "syncing") {
    return `正在同步阅读进度 · ${displayPercent}`;
  }

  if (syncState.value === "pending") {
    return `本地阅读到 ${displayPercent}，将于 15 秒内自动同步`;
  }

  if (syncState.value === "error") {
    return `同步失败，后续会继续重试 · ${displayPercent}`;
  }

  if (progress.value) {
    return `已同步到云端 ${formatPercent(progress.value.percent)} · 第 ${progress.value.chapter_index + 1} 章`;
  }

  return `当前进度 ${displayPercent}`;
});
const canGoPrev = computed(() => currentChapterIndex.value > 0);
const canGoNext = computed(() => currentChapterIndex.value < chapters.value.length - 1);
const readerStyleVars = computed(() => ({
  "--reader-font-size": `${preferences.fontSize}px`,
  "--reader-line-height": String(preferences.lineHeight),
  "--reader-letter-spacing": `${preferences.letterSpacing}px`,
  "--reader-paragraph-spacing": String(preferences.paragraphSpacing),
  "--reader-content-width": `${preferences.contentWidth}ch`,
  "--reader-content-width-mobile": `${mapReaderContentWidthForMobile(preferences.contentWidth)}%`,
}));

watch(
  preferences,
  (value) => {
    preferencesStore.patchReader(value);
  },
  { deep: true },
);

watch(
  () => props.bookId,
  () => {
    void loadReader();
  },
  { immediate: true },
);

watch(
  () => route.params.chapterIndex,
  (value, previousValue) => {
    if (value === previousValue || loading.value || chapterLoading.value || chapters.value.length === 0) {
      return;
    }

    const state = getRouteChapterState();
    if (!state.provided) {
      return;
    }

    const normalizedIndex = normalizeChapterIndex(state.value);
    if (normalizedIndex === currentChapterIndex.value) {
      return;
    }

    void openChapter(normalizedIndex, {
      syncRoute: !state.valid || normalizedIndex !== state.value,
      replace: true,
      smoothScroll: false,
      restoreCharOffset: 0,
    });
  },
);

onMounted(() => {
  if (typeof window === "undefined") {
    return;
  }

  syncViewportState();
  window.addEventListener("resize", handleWindowResize, { passive: true });
  window.addEventListener("scroll", handleWindowScroll, { passive: true });
  window.addEventListener("pagehide", handlePageHide);
});

onUnmounted(() => {
  clearScheduledProgressSync();

  if (typeof window === "undefined") {
    return;
  }

  window.removeEventListener("resize", handleWindowResize);
  window.removeEventListener("scroll", handleWindowScroll);
  window.removeEventListener("pagehide", handlePageHide);

  void preferencesStore.flushPendingPatch();
});

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}

function roundPercent(value: number) {
  return Number(value.toFixed(2));
}

function mapReaderContentWidthForMobile(contentWidth: number) {
  const ratio = clamp((contentWidth - 56) / (96 - 56), 0, 1);
  const percent = MOBILE_CONTENT_WIDTH_MIN_PERCENT
    + (MOBILE_CONTENT_WIDTH_MAX_PERCENT - MOBILE_CONTENT_WIDTH_MIN_PERCENT) * ratio;
  return Number(percent.toFixed(2));
}

function getRouteChapterState(): RouteChapterState {
  const raw = Array.isArray(route.params.chapterIndex)
    ? route.params.chapterIndex[0]
    : route.params.chapterIndex;

  if (raw === undefined) {
    return {
      provided: false,
      valid: true,
      value: 0,
    };
  }

  const parsed = Number(raw);
  return {
    provided: true,
    valid: Number.isFinite(parsed),
    value: Number.isFinite(parsed) ? parsed : 0,
  };
}

function normalizeChapterIndex(index: number) {
  if (chapters.value.length === 0) {
    return 0;
  }

  return clamp(index, 0, chapters.value.length - 1);
}

function formatChapterOrdinal(index: number) {
  return `第 ${index + 1} 章`;
}

function buildReaderChapterContentView(content: string, chapterTitle: string): ReaderChapterContentView {
  const normalizedContent = content || "";
  const normalizedTitle = chapterTitle.trim();

  if (!normalizedContent || !normalizedTitle) {
    return {
      body: normalizedContent,
      trimmedPrefixLength: 0,
    };
  }

  let cursor = 0;
  while (cursor < normalizedContent.length && isReaderChapterWhitespace(normalizedContent[cursor])) {
    cursor += 1;
  }

  if (!normalizedContent.startsWith(normalizedTitle, cursor)) {
    return {
      body: normalizedContent,
      trimmedPrefixLength: 0,
    };
  }

  const bodyOffset = cursor + normalizedTitle.length;
  if (bodyOffset < normalizedContent.length && !isReaderChapterWhitespace(normalizedContent[bodyOffset])) {
    return {
      body: normalizedContent,
      trimmedPrefixLength: 0,
    };
  }

  let bodyStart = bodyOffset;
  while (bodyStart < normalizedContent.length && isReaderChapterWhitespace(normalizedContent[bodyStart])) {
    bodyStart += 1;
  }

  return {
    body: normalizedContent.slice(bodyStart),
    trimmedPrefixLength: bodyStart,
  };
}

function buildReaderParagraphs(content: string) {
  if (!content) {
    return [];
  }

  const paragraphs = content
    .replace(/\r\n?/g, "\n")
    .split(/\n+/)
    .map((paragraph) => paragraph.replace(/^[\s\u3000]+/u, "").trim())
    .filter((paragraph) => paragraph.length > 0);

  return paragraphs.length > 0 ? paragraphs : [content.trim()];
}

function isReaderChapterWhitespace(character: string) {
  return /\s/.test(character) || character === "\uFEFF";
}

function syncViewportState() {
  if (typeof window === "undefined") {
    return;
  }

  viewportWidth.value = window.innerWidth;

  if (!isCompactViewport.value) {
    mobileChromeVisible.value = true;
    return;
  }

  if (!activeDrawer.value) {
    mobileChromeVisible.value = false;
  }
}

function handleWindowResize() {
  syncViewportState();
}

function openDrawer(view: ReaderDrawerView) {
  activeDrawer.value = view;
  mobileChromeVisible.value = true;
}

function handleReadingSurfaceTap() {
  if (!isCompactViewport.value || activeDrawer.value) {
    return;
  }

  mobileChromeVisible.value = !mobileChromeVisible.value;
}

function toProgressSnapshot(source: Pick<ReadingProgress, "chapter_index" | "char_offset" | "percent" | "updated_at">): ProgressSnapshot {
  return {
    chapter_index: source.chapter_index,
    char_offset: source.char_offset,
    percent: source.percent,
    updated_at: source.updated_at,
  };
}

function getProgressKey(snapshot: Pick<ProgressSnapshot, "chapter_index" | "char_offset">) {
  return `${props.bookId}:${snapshot.chapter_index}:${snapshot.char_offset}`;
}

function buildProgressSnapshotForPosition(
  chapterIndex: number,
  charOffset: number,
  chapterLength = currentChapter.value?.content.length || 0,
): ProgressSnapshot {
  const normalizedChapterIndex = normalizeChapterIndex(chapterIndex);
  const normalizedCharOffset = chapterLength > 0 ? clamp(charOffset, 0, chapterLength) : 0;
  const chapterRatio = chapterLength > 0 ? normalizedCharOffset / chapterLength : 0;
  const percent = chapters.value.length > 0
    ? roundPercent(((normalizedChapterIndex + chapterRatio) / chapters.value.length) * 100)
    : 0;

  return {
    chapter_index: normalizedChapterIndex,
    char_offset: normalizedCharOffset,
    percent,
    updated_at: new Date().toISOString(),
  };
}

function clearScheduledProgressSync() {
  if (!progressSaveTimer) {
    return;
  }

  clearTimeout(progressSaveTimer);
  progressSaveTimer = null;
}

function scheduleProgressSync() {
  if (typeof window === "undefined" || !currentChapter.value) {
    return;
  }

  if (syncState.value !== "syncing") {
    syncState.value = "pending";
  }

  if (progressSaveTimer) {
    return;
  }

  progressSaveTimer = window.setTimeout(() => {
    progressSaveTimer = null;
    void flushProgress("throttled");
  }, PROGRESS_THROTTLE_MS);
}

function getViewportCharOffset() {
  if (typeof window === "undefined" || !contentRef.value || !currentChapter.value) {
    return 0;
  }

  const chapterLength = currentChapter.value.content.length;
  if (chapterLength <= 0) {
    return 0;
  }

  const renderedLength = currentChapterBody.value.length;
  if (renderedLength <= 0) {
    return clamp(currentChapterTrimmedPrefixLength.value, 0, chapterLength);
  }

  const rect = contentRef.value.getBoundingClientRect();
  const elementTop = rect.top + window.scrollY;
  const scrollableHeight = Math.max(contentRef.value.scrollHeight - window.innerHeight * 0.58, 1);
  const focusY = window.scrollY + Math.min(window.innerHeight * 0.32, 220);
  const ratio = clamp((focusY - elementTop) / scrollableHeight, 0, 1);
  const renderedOffset = Math.round(renderedLength * ratio);

  return clamp(currentChapterTrimmedPrefixLength.value + renderedOffset, 0, chapterLength);
}

function captureCurrentProgressSnapshot() {
  if (!currentChapter.value) {
    return null;
  }

  return buildProgressSnapshotForPosition(
    currentChapterIndex.value,
    getViewportCharOffset(),
    currentChapter.value.content.length,
  );
}

function syncSessionProgressFromViewport() {
  const snapshot = captureCurrentProgressSnapshot();
  if (!snapshot) {
    return;
  }

  hasMeaningfulReadingActivity.value = true;
  sessionProgress.value = snapshot;
  scheduleProgressSync();
}

async function restoreScrollForCharOffset(charOffset: number, smoothScroll = false) {
  await nextTick();

  if (typeof window === "undefined" || !contentRef.value || !currentChapter.value) {
    return;
  }

  const renderedLength = currentChapterBody.value.length;
  const adjustedCharOffset = clamp(
    charOffset - currentChapterTrimmedPrefixLength.value,
    0,
    Math.max(renderedLength, 0),
  );
  const ratio = renderedLength > 0 ? clamp(adjustedCharOffset / renderedLength, 0, 1) : 0;
  const rect = contentRef.value.getBoundingClientRect();
  const elementTop = rect.top + window.scrollY;
  const scrollableHeight = Math.max(contentRef.value.scrollHeight - window.innerHeight * 0.58, 0);
  const targetTop = Math.max(0, elementTop - READER_SCROLL_ANCHOR + scrollableHeight * ratio);

  suppressScrollTrackingUntil = Date.now() + (smoothScroll ? 900 : 420);
  window.scrollTo({
    top: targetTop,
    behavior: smoothScroll ? "smooth" : "auto",
  });
}

async function loadProgressSafely(bookId: number) {
  try {
    return await booksApi.getProgress(bookId);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }

    throw error;
  }
}

async function loadBookDetailSafely(bookId: number) {
  try {
    return await booksApi.detail(bookId);
  } catch {
    return null;
  }
}

async function loadReader() {
  loading.value = true;
  pageError.value = null;
  chapterError.value = null;
  activeDrawer.value = null;
  mobileChromeVisible.value = !isCompactViewport.value;
  bookTitle.value = "";
  sessionProgress.value = null;
  hasMeaningfulReadingActivity.value = false;
  syncState.value = "idle";
  clearScheduledProgressSync();

  try {
    const [bookDetail, chapterList, latestProgress] = await Promise.all([
      loadBookDetailSafely(props.bookId),
      booksApi.chapters(props.bookId),
      loadProgressSafely(props.bookId),
    ]);

    bookTitle.value = bookDetail?.title || "";
    chapters.value = chapterList;
    progress.value = latestProgress;
    lastSavedProgressKey = latestProgress ? getProgressKey(latestProgress) : "";

    if (chapterList.length === 0) {
      currentChapter.value = null;
      currentChapterIndex.value = 0;
      return;
    }

    const routeState = getRouteChapterState();
    const shouldUseRouteChapter = routeState.provided && routeState.valid;
    const requestedIndex = shouldUseRouteChapter
      ? routeState.value
      : latestProgress?.chapter_index ?? 0;
    const normalizedIndex = normalizeChapterIndex(requestedIndex);
    const restoreCharOffset = shouldUseRouteChapter
      ? 0
      : latestProgress?.chapter_index === normalizedIndex
        ? latestProgress.char_offset
        : 0;
    const shouldSyncRoute = routeState.provided
      ? !routeState.valid || normalizedIndex !== routeState.value
      : normalizedIndex !== 0;

    await openChapter(normalizedIndex, {
      syncRoute: shouldSyncRoute,
      replace: true,
      smoothScroll: false,
      restoreCharOffset,
    });
  } catch (error) {
    bookTitle.value = "";
    chapters.value = [];
    progress.value = null;
    sessionProgress.value = null;
    currentChapter.value = null;
    pageError.value = getErrorMessage(error);
  } finally {
    loading.value = false;
  }
}

async function flushProgress(
  _reason: string,
  options: {
    snapshot?: ProgressSnapshot | null;
    keepalive?: boolean;
    force?: boolean;
  } = {},
) {
  const snapshot = options.snapshot ?? sessionProgress.value ?? captureCurrentProgressSnapshot();
  if (!snapshot) {
    return;
  }

  sessionProgress.value = snapshot;
  const snapshotKey = getProgressKey(snapshot);

  if (!options.force && snapshotKey === lastSavedProgressKey) {
    if (syncState.value !== "error") {
      syncState.value = "idle";
    }
    return;
  }

  clearScheduledProgressSync();

  if (options.keepalive) {
    attemptKeepaliveProgressSave(snapshot);
    return;
  }

  if (saveInFlight) {
    queuedSnapshot = snapshot;
    return;
  }

  saveInFlight = true;
  syncState.value = "syncing";

  try {
    const saved = await booksApi.saveProgress(props.bookId, snapshot);
    progress.value = saved;
    sessionProgress.value = toProgressSnapshot(saved);
    lastSavedProgressKey = getProgressKey(saved);
    syncState.value = "idle";
  } catch {
    syncState.value = "error";
  } finally {
    saveInFlight = false;

    if (queuedSnapshot) {
      const nextSnapshot = queuedSnapshot;
      queuedSnapshot = null;

      if (getProgressKey(nextSnapshot) !== lastSavedProgressKey) {
        void flushProgress("queued", {
          snapshot: nextSnapshot,
          force: true,
        });
      }
    }
  }
}

function attemptKeepaliveProgressSave(snapshot: ProgressSnapshot) {
  if (typeof window === "undefined") {
    return;
  }

  const snapshotKey = getProgressKey(snapshot);
  if (snapshotKey === lastSavedProgressKey) {
    return;
  }

  const token = authTokenStorage.get();
  const headers = new Headers({
    "Content-Type": "application/json",
  });

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  void fetch(buildApiUrl(`/api/books/${props.bookId}/progress`), {
    method: "PUT",
    headers,
    body: JSON.stringify(snapshot),
    keepalive: true,
  });
}

async function openChapter(
  chapterIndex: number,
  options: {
    syncRoute?: boolean;
    replace?: boolean;
    smoothScroll?: boolean;
    restoreCharOffset?: number;
    saveAfterOpen?: boolean;
  } = {},
) {
  if (chapters.value.length === 0) {
    return;
  }

  const normalizedIndex = normalizeChapterIndex(chapterIndex);
  chapterLoading.value = true;
  chapterError.value = null;

  try {
    const content = await booksApi.chapterContent(props.bookId, normalizedIndex);
    const restoreCharOffset = clamp(
      options.restoreCharOffset ?? 0,
      0,
      content.content.length,
    );

    currentChapter.value = content;
    currentChapterIndex.value = normalizedIndex;
    sessionProgress.value = buildProgressSnapshotForPosition(
      normalizedIndex,
      restoreCharOffset,
      content.content.length,
    );

    if (options.syncRoute) {
      await router[options.replace ? "replace" : "push"]({
        name: "reader",
        params: {
          bookId: props.bookId,
          chapterIndex: normalizedIndex,
        },
      });
    }

    await restoreScrollForCharOffset(restoreCharOffset, !!options.smoothScroll);

    if (options.saveAfterOpen && sessionProgress.value) {
      hasMeaningfulReadingActivity.value = true;
      await flushProgress("chapter-change", {
        snapshot: sessionProgress.value,
        force: true,
      });
    }
  } catch (error) {
    const message = getErrorMessage(error);

    if (!currentChapter.value) {
      pageError.value = message;
    } else {
      chapterError.value = message;
    }
  } finally {
    chapterLoading.value = false;
  }
}

function handleWindowScroll() {
  if (
    typeof window === "undefined" ||
    loading.value ||
    chapterLoading.value ||
    !currentChapter.value ||
    Date.now() < suppressScrollTrackingUntil
  ) {
    return;
  }

  syncSessionProgressFromViewport();

  if (isCompactViewport.value && mobileChromeVisible.value && !activeDrawer.value) {
    mobileChromeVisible.value = false;
  }
}

function handlePageHide() {
  void preferencesStore.flushPendingPatch();

  if (!hasMeaningfulReadingActivity.value) {
    return;
  }

  void flushProgress("pagehide", {
    keepalive: true,
    force: true,
  });
}

function handleChapterSelect(chapterIndex: number) {
  activeDrawer.value = null;

  if (isCompactViewport.value) {
    mobileChromeVisible.value = false;
  }

  void openChapter(chapterIndex, {
    syncRoute: true,
    smoothScroll: false,
    restoreCharOffset: 0,
    saveAfterOpen: true,
  });
}

function handlePrevChapter() {
  if (!canGoPrev.value) {
    return;
  }

  handleChapterSelect(currentChapterIndex.value - 1);
}

function handleNextChapter() {
  if (!canGoNext.value) {
    return;
  }

  handleChapterSelect(currentChapterIndex.value + 1);
}

function goBack() {
  void router.push({
    name: "book-detail",
    params: { bookId: props.bookId },
  });
}
</script>

<style scoped>
.reader-page {
  --reader-font-size: 19px;
  --reader-line-height: 1.95;
   --reader-letter-spacing: 0px;
   --reader-paragraph-spacing: 1;
   --reader-content-width: 72ch;
  --reader-column-max: 960px;
  --reader-side-width: 192px;
  --reader-side-gap: clamp(18px, 2vw, 24px);
  --reader-page-gutter: clamp(18px, 2.2vw, 30px);
  --reader-column-width: min(
    var(--reader-column-max),
    calc(
      100vw - (var(--reader-page-gutter) * 2) - (var(--reader-side-width) * 2) - (var(--reader-side-gap) * 2)
    )
  );
  min-height: 100dvh;
  padding: var(--reader-page-gutter);
  background:
    radial-gradient(circle at 14% 10%, rgba(184, 93, 54, 0.16), transparent 22%),
    radial-gradient(circle at 86% 16%, rgba(52, 107, 97, 0.12), transparent 24%),
    radial-gradient(circle at 50% 100%, rgba(255, 255, 255, 0.2), transparent 32%),
    var(--reader-page-bg);
  color: var(--reader-body);
}

.reader-page--light {
  --reader-page-bg: linear-gradient(180deg, #f7efe2 0%, #efe3d0 100%);
  --reader-panel-bg: rgba(255, 250, 243, 0.74);
  --reader-panel-border: rgba(109, 90, 74, 0.12);
  --reader-panel-shadow: 0 24px 60px rgba(82, 55, 28, 0.12);
  --reader-paper-bg:
    linear-gradient(180deg, rgba(255, 255, 255, 0.78), rgba(255, 250, 243, 0.92)),
    linear-gradient(135deg, rgba(255, 255, 255, 0.28), rgba(255, 255, 255, 0));
  --reader-paper-border: rgba(109, 90, 74, 0.12);
  --reader-paper-shadow: 0 30px 80px rgba(82, 55, 28, 0.12);
  --reader-heading: #2f241d;
  --reader-body: #43362b;
  --reader-muted: #7a6655;
  --reader-accent: #b85d36;
  --reader-progress-rail: rgba(184, 93, 54, 0.14);
  --reader-action-bg: rgba(255, 255, 255, 0.58);
  --reader-action-hover: rgba(255, 255, 255, 0.86);
  --reader-settings-bg: rgba(255, 255, 255, 0.56);
  --reader-settings-border: rgba(109, 90, 74, 0.08);
}

.reader-page--dark {
  --reader-page-bg: linear-gradient(180deg, #171411 0%, #0e0c0a 100%);
  --reader-panel-bg: rgba(34, 29, 24, 0.72);
  --reader-panel-border: rgba(243, 230, 215, 0.09);
  --reader-panel-shadow: 0 24px 64px rgba(0, 0, 0, 0.38);
  --reader-paper-bg:
    linear-gradient(180deg, rgba(35, 30, 25, 0.92), rgba(24, 20, 17, 0.98)),
    linear-gradient(135deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0));
  --reader-paper-border: rgba(243, 230, 215, 0.08);
  --reader-paper-shadow: 0 34px 88px rgba(0, 0, 0, 0.42);
  --reader-heading: #f3e7d9;
  --reader-body: #dccbbb;
  --reader-muted: #baa795;
  --reader-accent: #d68d5e;
  --reader-progress-rail: rgba(214, 141, 94, 0.18);
  --reader-action-bg: rgba(255, 255, 255, 0.04);
  --reader-action-hover: rgba(255, 255, 255, 0.08);
  --reader-settings-bg: rgba(255, 255, 255, 0.04);
  --reader-settings-border: rgba(243, 230, 215, 0.08);
}

.reader-shell {
  position: relative;
}

.reader-loading {
  display: grid;
  grid-template-columns: var(--reader-side-width) minmax(0, var(--reader-column-width)) var(--reader-side-width);
  justify-content: center;
  gap: var(--reader-side-gap);
  align-items: start;
}

.reader-loading__main {
  display: grid;
  gap: 20px;
}

.reader-loading__panel,
.reader-loading__paper {
  padding: 20px;
}

.reader-glass {
  border: 1px solid var(--reader-panel-border);
  border-radius: 28px;
  background: var(--reader-panel-bg);
  box-shadow: var(--reader-panel-shadow);
  backdrop-filter: blur(18px);
}

.reader-paper {
  position: relative;
  overflow: hidden;
  width: min(100%, var(--reader-column-width));
  max-width: var(--reader-column-width);
  margin: 0 auto;
  padding: clamp(28px, 4vw, 54px);
  border: 1px solid var(--reader-paper-border);
  border-radius: 34px;
  background: var(--reader-paper-bg);
  box-shadow: var(--reader-paper-shadow);
}

.reader-paper::before {
  content: "";
  position: absolute;
  inset: 0;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.12), transparent 18%),
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.12), transparent 28%);
  pointer-events: none;
}

.reader-page__alert {
  margin-bottom: 22px;
  border-radius: 18px;
}

.reader-rail,
.reader-float {
  position: fixed;
  top: 50%;
  z-index: 24;
  transform: translateY(-50%);
}

.reader-rail {
  left: calc(50% - (var(--reader-column-width) / 2) - var(--reader-side-width) - var(--reader-side-gap));
  width: var(--reader-side-width);
}

.reader-float {
  left: calc(50% + (var(--reader-column-width) / 2) + var(--reader-side-gap));
  width: var(--reader-side-width);
}

.reader-rail__panel,
.reader-float__panel {
  width: 100%;
  max-height: calc(100dvh - 48px);
  padding: 16px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-x: hidden;
  overflow-y: auto;
}

.reader-rail__panel,
.reader-rail__brand,
.reader-rail__actions,
.reader-rail__action,
.reader-float__panel,
.reader-float__actions {
  min-width: 0;
}

.reader-rail__brand {
  display: grid;
  gap: 6px;
}

.reader-eyebrow {
  display: inline-flex;
  width: fit-content;
  max-width: 100%;
  padding: 6px 12px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--reader-accent) 16%, transparent);
  color: var(--reader-accent);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.reader-rail__chapter {
  color: var(--reader-heading);
  font-size: 16px;
  line-height: 1.5;
}

.reader-rail__sync {
  color: var(--reader-muted);
  font-size: 12px;
}

.reader-rail__actions,
.reader-float__actions {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.reader-rail__action {
  width: 100%;
  max-width: 100%;
  min-width: 0;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
  padding: 12px 14px;
  border: 1px solid transparent;
  border-radius: 18px;
  background: var(--reader-action-bg);
  color: inherit;
  text-align: left;
  cursor: pointer;
  transition:
    transform 180ms ease,
    background 180ms ease,
    border-color 180ms ease;
}

.reader-rail__action:hover {
  transform: translateY(-1px);
  background: var(--reader-action-hover);
  border-color: color-mix(in srgb, var(--reader-accent) 22%, transparent);
}

.reader-rail__action strong,
.reader-rail__action span {
  width: 100%;
  max-width: 100%;
  overflow-wrap: anywhere;
}

.reader-rail__action strong {
  color: var(--reader-heading);
  font-size: 15px;
}

.reader-rail__action span {
  color: var(--reader-muted);
  font-size: 12px;
  line-height: 1.5;
}

.reader-stage {
  width: 100%;
  min-width: 0;
  display: grid;
  gap: 24px;
}

.reader-stage__hero {
  width: min(100%, var(--reader-column-width));
  max-width: var(--reader-column-width);
  margin: 0 auto;
  display: grid;
  gap: 14px;
  padding-top: 20px;
}

.reader-stage__header {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  align-items: end;
}

.reader-stage__chapter {
  margin: 0;
  color: var(--reader-muted);
  font-size: 14px;
}

.reader-stage__book {
  margin: 0 0 8px;
  color: var(--reader-muted);
  font-size: 13px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.reader-stage__title {
  margin: 10px 0 0;
  color: var(--reader-heading);
  font-family: var(--font-display);
  font-size: clamp(34px, 5vw, 62px);
  line-height: 1.02;
}

.reader-stage__stat {
  min-width: 160px;
  display: grid;
  gap: 4px;
  justify-items: end;
}

.reader-stage__stat span,
.reader-stage__stat small,
.reader-drawer__summary p,
.reader-float__summary {
  color: var(--reader-muted);
}

.reader-stage__stat strong {
  color: var(--reader-heading);
  font-size: clamp(28px, 4vw, 40px);
  line-height: 1;
}

.reader-drawer__summary {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: baseline;
}

.reader-drawer__summary span,
.reader-float__stat span {
  color: var(--reader-muted);
  font-size: 13px;
}

.reader-drawer__summary strong,
.reader-float__stat strong {
  color: var(--reader-heading);
  font-size: 28px;
  line-height: 1;
}

.reader-content {
  position: relative;
  width: min(100%, var(--reader-content-width));
  max-width: 100%;
  margin: 0 auto;
  color: var(--reader-body);
  font-size: var(--reader-font-size);
  line-height: var(--reader-line-height);
  letter-spacing: var(--reader-letter-spacing);
  word-break: break-word;
  transition: opacity 180ms ease;
}

.reader-content__paragraph {
  margin: 0;
  text-indent: 2em;
  white-space: pre-wrap;
  word-break: break-word;
}

.reader-content__paragraph + .reader-content__paragraph {
  margin-top: calc(var(--reader-font-size) * var(--reader-line-height) * var(--reader-paragraph-spacing));
}

.reader-content--dimmed {
  opacity: 0.56;
}

.reader-content--loading {
  display: grid;
  gap: 12px;
}

.reader-paper__chapter-nav {
  margin-top: 28px;
  padding-top: 18px;
  border-top: 1px solid color-mix(in srgb, var(--reader-paper-border) 88%, transparent);
}

.reader-paper__chapter-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.reader-float__panel {
  gap: 16px;
}

.reader-float__stat {
  display: grid;
  gap: 6px;
}

.reader-float__summary {
  display: grid;
  gap: 4px;
  font-size: 13px;
  line-height: 1.7;
}

.reader-drawer__summary {
  display: grid;
  gap: 8px;
}

.reader-drawer__progress {
  margin-top: 18px;
}

.reader-catalog__list {
  display: grid;
  gap: 10px;
  min-height: 0;
  overflow-y: auto;
  padding-right: 4px;
}

.reader-catalog__list--drawer {
  max-height: calc(100dvh - 240px);
  margin-top: 18px;
}

.reader-catalog__item {
  display: grid;
  gap: 6px;
  padding: 14px 16px;
  border: 1px solid transparent;
  border-radius: 18px;
  background: var(--reader-action-bg);
  color: inherit;
  text-align: left;
  cursor: pointer;
  transition:
    transform 180ms ease,
    border-color 180ms ease,
    background 180ms ease;
}

.reader-catalog__item:hover {
  transform: translateY(-1px);
  border-color: color-mix(in srgb, var(--reader-accent) 24%, transparent);
}

.reader-catalog__item--active {
  border-color: color-mix(in srgb, var(--reader-accent) 28%, transparent);
  background: color-mix(in srgb, var(--reader-accent) 12%, var(--reader-action-bg));
}

.reader-catalog__index {
  color: var(--reader-muted);
  font-size: 12px;
}

.reader-catalog__title {
  color: var(--reader-heading);
  line-height: 1.6;
}

.reader-settings {
  display: grid;
  gap: 16px;
}

.reader-settings__group {
  display: grid;
  gap: 14px;
  padding: 18px;
  border: 1px solid var(--reader-settings-border);
  border-radius: 22px;
  background: var(--reader-settings-bg);
}

.reader-settings__label-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: baseline;
}

.reader-settings__label-row span {
  color: var(--reader-muted);
  font-size: 13px;
}

.reader-settings__label-row strong {
  color: var(--reader-heading);
  font-size: 16px;
}

@media (max-width: 1320px) {
  .reader-page {
    --reader-side-width: 184px;
    --reader-side-gap: 18px;
  }
}

@media (max-width: 1120px) {
  .reader-page {
    --reader-side-width: 168px;
  }

  .reader-rail__panel,
  .reader-float__panel {
    padding: 14px;
  }

  .reader-rail__action {
    padding: 11px 12px;
  }
}

@media (max-width: 980px) {
  .reader-page {
    --reader-column-width: 100%;
    padding: 0;
  }

  .reader-shell,
  .reader-loading {
    grid-template-columns: 1fr;
    gap: 0;
  }

  .reader-loading__panel--rail,
  .reader-loading__panel--float {
    display: none;
  }

  .reader-loading__main {
    padding: 18px;
  }

  .reader-stage {
    min-height: 100dvh;
    gap: 18px;
  }

  .reader-stage__hero,
  .reader-paper {
    width: auto;
    max-width: none;
  }

  .reader-stage__hero {
    padding: 26px 18px 0;
  }

  .reader-stage__header {
    flex-direction: column;
    align-items: stretch;
  }

  .reader-stage__stat {
    display: none;
  }

  .reader-paper {
    margin: 0 10px;
    padding: 26px 20px 30px;
    border-radius: 30px;
  }

  .reader-float {
    display: none;
  }

  .reader-rail {
    position: fixed;
    top: 14px;
    left: 14px;
    z-index: 30;
    width: min(260px, calc(100vw - 28px));
    opacity: 0;
    pointer-events: none;
    transform: translateY(-10px);
    transition:
      opacity 180ms ease,
      transform 180ms ease;
  }

  .reader-rail--active {
    opacity: 1;
    pointer-events: auto;
    transform: translateY(0);
  }
}

@media (max-width: 720px) {
  .reader-stage__title {
    font-size: clamp(30px, 8vw, 42px);
  }

  .reader-content {
    width: var(--reader-content-width-mobile);
  }

  .reader-drawer__summary {
    display: grid;
    gap: 8px;
  }
}
</style>
