<template>
  <div class="reader-page" :class="`reader-page--${preferences.theme}`" :style="readerStyleVars">
    <div v-if="loading" class="reader-page__state">
      <n-skeleton text :repeat="10" />
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
      description="可以先回到书籍详情页查看目录，或稍后再刷新一次。"
    >
      <template #action>
        <n-button secondary @click="loadReader">重新加载</n-button>
        <n-button tertiary @click="goBack">返回详情</n-button>
      </template>
    </page-status-panel>

    <template v-else>
      <section class="reader-header">
        <div>
          <p v-if="bookTitle" class="reader-header__book">{{ bookTitle }}</p>
          <h1 class="reader-header__title">{{ currentChapterTitle }}</h1>
          <p class="reader-header__meta">{{ currentChapterPositionLabel }} · {{ progressPercentLabel }}</p>
        </div>
        <div class="reader-header__actions">
          <n-button secondary @click="openDrawer('catalog')">目录</n-button>
          <n-button secondary @click="openDrawer('settings')">设置</n-button>
          <n-button tertiary @click="goBack">返回详情</n-button>
        </div>
      </section>

      <section class="reader-paper">
        <n-alert v-if="chapterError" type="error" :show-icon="false" class="reader-paper__alert">
          {{ chapterError }}
        </n-alert>

        <article ref="contentRef" class="reader-content" :class="{ 'reader-content--loading': chapterLoading }">
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

        <div class="reader-footer">
          <div class="reader-footer__progress">
            <span>{{ syncedProgressLabel }}</span>
            <n-progress
              type="line"
              :percentage="currentProgressPercent"
              :show-indicator="false"
              color="var(--reader-accent)"
              rail-color="var(--reader-progress-rail)"
            />
          </div>

          <div class="reader-footer__actions">
            <n-button :disabled="!canGoPrev || chapterLoading" @click="handlePrevChapter">上一章</n-button>
            <n-button type="primary" :disabled="!canGoNext || chapterLoading" @click="handleNextChapter">
              下一章
            </n-button>
          </div>
        </div>
      </section>
    </template>

    <n-drawer v-model:show="isDrawerOpen" placement="left" :width="drawerWidth">
      <n-drawer-content :title="drawerTitle" closable body-content-style="padding: 20px;">
        <template v-if="activeDrawer === 'catalog'">
          <div class="reader-catalog">
            <button
              v-for="chapter in chapters"
              :key="chapter.id"
              type="button"
              class="reader-catalog__item"
              :class="{ 'reader-catalog__item--active': chapter.chapter_index === currentChapterIndex }"
              @click="handleChapterSelect(chapter.chapter_index)"
            >
              <span>{{ formatChapterOrdinal(chapter.chapter_index) }}</span>
              <strong>{{ chapter.chapter_title }}</strong>
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

import PageStatusPanel from "../components/PageStatusPanel.vue";
import { useReaderSource } from "../composables/useReaderSource";
import { usePreferencesStore } from "../stores/preferences";
import type { BookChapter, BookChapterContent, ReadingProgress, ReadingProgressPayload } from "../types/api";
import { formatPercent } from "../utils/format";

const PROGRESS_THROTTLE_MS = 15000;
const COMPACT_BREAKPOINT = 980;

type ProgressSnapshot = ReadingProgressPayload;
type ReaderDrawerView = "catalog" | "settings";

const props = withDefaults(defineProps<{ libraryBookId: string; chapterIndex?: number }>(), { chapterIndex: 0 });

const route = useRoute();
const router = useRouter();
const preferencesStore = usePreferencesStore();
const chapters = ref<BookChapter[]>([]);
const bookTitle = ref("");
const progress = ref<ReadingProgress | null>(null);
const sessionProgress = ref<ProgressSnapshot | null>(null);
const currentChapter = ref<BookChapterContent | null>(null);
const currentChapterIndex = ref(0);
const loading = ref(true);
const chapterLoading = ref(false);
const pageError = ref<string | null>(null);
const chapterError = ref<string | null>(null);
const syncState = ref<"idle" | "pending" | "syncing" | "error">("idle");
const activeDrawer = ref<ReaderDrawerView | null>(null);
const viewportWidth = ref(COMPACT_BREAKPOINT + 200);
const contentRef = ref<HTMLElement | null>(null);
const preferences = reactive({ ...preferencesStore.reader });

let progressSaveTimer: ReturnType<typeof setTimeout> | null = null;
let lastSavedProgressKey = "";

const currentChapterTitle = computed(() => currentChapter.value?.chapter_title || chapters.value[currentChapterIndex.value]?.chapter_title || "正在载入章节");
const currentChapterParagraphs = computed(() => {
  const content = currentChapter.value?.content || "";
  return content.split(/\n{2,}/).map((item) => item.trim()).filter(Boolean);
});
const currentChapterPositionLabel = computed(() => chapters.value.length === 0 ? "暂无目录" : `第 ${currentChapterIndex.value + 1} / ${chapters.value.length} 章`);
const currentProgressPercent = computed(() => sessionProgress.value?.percent ?? progress.value?.percent ?? 0);
const progressPercentLabel = computed(() => formatPercent(currentProgressPercent.value));
const syncedProgressLabel = computed(() => `${syncState.value === "error" ? "同步待重试" : "当前进度"} · ${progressPercentLabel.value}`);
const canGoPrev = computed(() => currentChapterIndex.value > 0);
const canGoNext = computed(() => currentChapterIndex.value < chapters.value.length - 1);
const drawerTitle = computed(() => activeDrawer.value === "settings" ? "阅读设置" : "章节目录");
const drawerWidth = computed(() => Math.min(Math.max(viewportWidth.value - 24, 280), 380));
const isDrawerOpen = computed({
  get: () => activeDrawer.value !== null,
  set: (value: boolean) => {
    if (!value) {
      activeDrawer.value = null;
    }
  },
});
const readerStyleVars = computed(() => ({
  "--reader-font-size": `${preferences.fontSize}px`,
  "--reader-line-height": String(preferences.lineHeight),
  "--reader-progress-rail": "rgba(184, 93, 54, 0.14)",
  "--reader-accent": "var(--primary-color)",
}));

watch(
  preferences,
  (value) => {
    preferencesStore.patchReader(value);
  },
  { deep: true },
);

watch(
  () => props.libraryBookId,
  () => {
    void loadReader();
  },
  { immediate: true },
);

watch(
  () => route.params.chapterIndex,
  (value, oldValue) => {
    if (value === oldValue || loading.value || chapterLoading.value || chapters.value.length === 0) {
      return;
    }
    const raw = Array.isArray(value) ? value[0] : value;
    if (raw === undefined) {
      return;
    }
    const nextIndex = Number(raw);
    if (Number.isFinite(nextIndex) && normalizeChapterIndex(nextIndex) !== currentChapterIndex.value) {
      void openChapter(nextIndex, { syncRoute: false, restoreCharOffset: 0 });
    }
  },
);

onMounted(() => {
  if (typeof window === "undefined") {
    return;
  }
  viewportWidth.value = window.innerWidth;
  window.addEventListener("resize", handleWindowResize, { passive: true });
  window.addEventListener("scroll", handleWindowScroll, { passive: true });
  window.addEventListener("pagehide", handlePageHide);
});

onUnmounted(() => {
  if (typeof window === "undefined") {
    return;
  }
  window.removeEventListener("resize", handleWindowResize);
  window.removeEventListener("scroll", handleWindowScroll);
  window.removeEventListener("pagehide", handlePageHide);
  clearScheduledProgressSync();
});

function normalizeChapterIndex(index: number) {
  if (chapters.value.length === 0) {
    return 0;
  }
  return Math.min(Math.max(index, 0), chapters.value.length - 1);
}

function formatChapterOrdinal(index: number) {
  return `第 ${index + 1} 章`;
}

function openDrawer(drawer: ReaderDrawerView) {
  activeDrawer.value = drawer;
}

function handleWindowResize() {
  viewportWidth.value = window.innerWidth;
}

function buildProgressSnapshot(contentLength: number, chapterIndex = currentChapterIndex.value, charOffset = 0): ProgressSnapshot {
  const safeLength = Math.max(contentLength, 1);
  const percent = chapters.value.length === 0 ? 0 : Number((((chapterIndex + charOffset / safeLength) / chapters.value.length) * 100).toFixed(2));
  return {
    chapter_index: chapterIndex,
    char_offset: charOffset,
    percent,
    updated_at: new Date().toISOString(),
  };
}

function getProgressKey(snapshot: ProgressSnapshot) {
  return `${props.libraryBookId}:${snapshot.chapter_index}:${snapshot.char_offset}`;
}

function clearScheduledProgressSync() {
  if (progressSaveTimer) {
    clearTimeout(progressSaveTimer);
    progressSaveTimer = null;
  }
}

function scheduleProgressSync() {
  clearScheduledProgressSync();
  progressSaveTimer = setTimeout(() => {
    progressSaveTimer = null;
    void flushProgress();
  }, PROGRESS_THROTTLE_MS);
}

async function loadReader() {
  loading.value = true;
  pageError.value = null;
  chapterError.value = null;
  activeDrawer.value = null;
  sessionProgress.value = null;
  clearScheduledProgressSync();

  try {
    const readerSource = useReaderSource(props.libraryBookId);
    const [resolvedBookTitle, chapterList, latestProgress] = await Promise.all([
      readerSource.loadDisplayTitle(),
      readerSource.loadCatalog(),
      readerSource.loadProgress(),
    ]);
    bookTitle.value = resolvedBookTitle;
    chapters.value = chapterList;
    progress.value = latestProgress;
    lastSavedProgressKey = latestProgress ? getProgressKey(latestProgress) : "";

    if (chapters.value.length === 0) {
      currentChapter.value = null;
      currentChapterIndex.value = 0;
      return;
    }

    const raw = Array.isArray(route.params.chapterIndex) ? route.params.chapterIndex[0] : route.params.chapterIndex;
    const nextIndex = raw !== undefined && Number.isFinite(Number(raw))
      ? Number(raw)
      : latestProgress?.chapter_index ?? 0;
    await openChapter(nextIndex, {
      syncRoute: raw === undefined,
      restoreCharOffset: latestProgress?.chapter_index === normalizeChapterIndex(nextIndex) ? latestProgress.char_offset : 0,
    });
  } catch (error) {
    chapters.value = [];
    currentChapter.value = null;
    progress.value = null;
    pageError.value = error instanceof Error ? error.message : "阅读页加载失败";
  } finally {
    loading.value = false;
  }
}

async function openChapter(
  chapterIndex: number,
  options: {
    syncRoute?: boolean;
    restoreCharOffset?: number;
    saveAfterOpen?: boolean;
  } = {},
) {
  const normalizedIndex = normalizeChapterIndex(chapterIndex);
  chapterLoading.value = true;
  chapterError.value = null;

  try {
    const content = await useReaderSource(props.libraryBookId).loadChapterContent(normalizedIndex);
    currentChapter.value = content;
    currentChapterIndex.value = normalizedIndex;
    const restoreCharOffset = Math.min(Math.max(options.restoreCharOffset || 0, 0), content.content.length);
    sessionProgress.value = buildProgressSnapshot(content.content.length, normalizedIndex, restoreCharOffset);

    if (options.syncRoute) {
      await router.replace({
        name: "reader",
        params: {
          libraryBookId: props.libraryBookId,
          chapterIndex: normalizedIndex,
        },
      });
    }

    await nextTick();
    if (typeof window !== "undefined") {
      const ratio = content.content.length === 0 ? 0 : restoreCharOffset / content.content.length;
      const scrollableHeight = Math.max(document.documentElement.scrollHeight - (window.innerHeight || 1), 1);
      window.scrollTo({ top: Math.round(scrollableHeight * ratio), behavior: "auto" });
    }

    if (options.saveAfterOpen) {
      await flushProgress(true);
    }
  } catch (error) {
    chapterError.value = error instanceof Error ? error.message : "章节加载失败";
  } finally {
    chapterLoading.value = false;
  }
}

async function flushProgress(force = false) {
  if (!sessionProgress.value) {
    return;
  }
  if (!force && getProgressKey(sessionProgress.value) === lastSavedProgressKey) {
    syncState.value = "idle";
    return;
  }

  try {
    syncState.value = "syncing";
    const saved = await useReaderSource(props.libraryBookId).saveProgress(sessionProgress.value);
    progress.value = saved;
    sessionProgress.value = {
      chapter_index: saved.chapter_index,
      char_offset: saved.char_offset,
      percent: saved.percent,
      updated_at: saved.updated_at,
    };
    lastSavedProgressKey = getProgressKey(sessionProgress.value);
    syncState.value = "idle";
  } catch {
    syncState.value = "error";
  }
}

function handleWindowScroll() {
  if (loading.value || chapterLoading.value || !currentChapter.value || typeof window === "undefined") {
    return;
  }
  const viewportHeight = window.innerHeight || 1;
  const scrollableHeight = Math.max(document.documentElement.scrollHeight - viewportHeight, 1);
  const ratio = Math.min(Math.max(window.scrollY / scrollableHeight, 0), 1);
  const charOffset = Math.round(currentChapter.value.content.length * ratio);
  sessionProgress.value = buildProgressSnapshot(currentChapter.value.content.length, currentChapterIndex.value, charOffset);
  syncState.value = "pending";
  scheduleProgressSync();
}

function handlePageHide() {
  if (sessionProgress.value) {
    void flushProgress(true);
  }
}

function handleChapterSelect(chapterIndex: number) {
  activeDrawer.value = null;
  void openChapter(chapterIndex, { syncRoute: true, restoreCharOffset: 0, saveAfterOpen: true });
}

function handlePrevChapter() {
  if (canGoPrev.value) {
    handleChapterSelect(currentChapterIndex.value - 1);
  }
}

function handleNextChapter() {
  if (canGoNext.value) {
    handleChapterSelect(currentChapterIndex.value + 1);
  }
}

function goBack() {
  void router.push({ name: "book-detail", params: { libraryBookId: props.libraryBookId } });
}
</script>

<style scoped>
.reader-page {
  min-height: 100vh;
  padding: 24px;
  background: var(--surface-color);
}

.reader-page__state {
  width: min(920px, 100%);
  margin: 0 auto;
  padding: 24px;
  border-radius: 24px;
  background: var(--surface-raised);
}

.reader-header {
  width: min(920px, 100%);
  margin: 0 auto 24px;
  display: flex;
  justify-content: space-between;
  gap: 24px;
  align-items: start;
}

.reader-header__book,
.reader-header__meta {
  margin: 0;
  color: var(--text-secondary);
}

.reader-header__title {
  margin: 8px 0;
  font-family: var(--font-display);
  font-size: clamp(28px, 4vw, 44px);
}

.reader-header__actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.reader-paper {
  width: min(920px, 100%);
  margin: 0 auto;
  padding: 28px;
  border-radius: 28px;
  background: var(--surface-raised);
  box-shadow: var(--shadow-soft);
}

.reader-paper__alert {
  margin-bottom: 16px;
}

.reader-content {
  min-height: 240px;
  font-size: var(--reader-font-size);
  line-height: calc(var(--reader-line-height) * 1em);
  letter-spacing: var(--reader-letter-spacing);
  transition: opacity 180ms ease;
}

.reader-content--loading {
  opacity: 0.56;
}

.reader-content__paragraph {
  margin: 0;
  white-space: pre-wrap;
}

.reader-content__paragraph + .reader-content__paragraph {
  margin-top: 1.2em;
}

.reader-footer {
  margin-top: 24px;
  display: grid;
  gap: 16px;
}

.reader-footer__actions {
  display: flex;
  gap: 12px;
}

.reader-catalog {
  display: grid;
  gap: 12px;
}

.reader-catalog__item {
  display: grid;
  gap: 6px;
  padding: 14px 16px;
  border: 1px solid var(--border-color-soft);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.82);
  text-align: left;
}

.reader-catalog__item--active {
  border-color: rgba(184, 93, 54, 0.28);
  background: rgba(184, 93, 54, 0.08);
}

.reader-settings {
  display: grid;
  gap: 16px;
}

.reader-settings__group {
  display: grid;
  gap: 14px;
  padding: 18px;
  border: 1px solid var(--border-color-soft);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.56);
}

.reader-settings__label-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

@media (max-width: 820px) {
  .reader-page {
    padding: 16px;
  }

  .reader-header {
    flex-direction: column;
  }

  .reader-footer__actions {
    display: grid;
    grid-template-columns: 1fr;
  }
}
</style>
