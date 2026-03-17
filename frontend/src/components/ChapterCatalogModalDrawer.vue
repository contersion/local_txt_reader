<template>
  <n-drawer
    v-if="isCompactViewport"
    :show="show"
    placement="right"
    :width="drawerWidth"
    :auto-focus="false"
    @update:show="handleShowChange"
  >
    <n-drawer-content title="目录" closable body-content-style="padding: 20px;">
      <section class="chapter-catalog-panel chapter-catalog-panel--drawer">
        <div class="chapter-catalog-panel__summary">
          <div class="chapter-catalog-panel__heading">
            <strong>目录</strong>
            <span class="chapter-catalog-panel__count">{{ chapterCountLabel }}</span>
          </div>
          <p v-if="bookTitle" class="chapter-catalog-panel__book">{{ bookTitle }}</p>
          <p class="chapter-catalog-panel__hint">
            点击任意章节后会直接跳转到阅读页，并自动关闭目录面板。
          </p>
        </div>

        <div class="chapter-catalog-panel__body">
          <n-empty
            v-if="chapters.length === 0"
            description="当前还没有可展示的目录，请稍后再试或重新解析目录。"
            class="chapter-catalog-panel__empty"
          />

          <div v-else class="chapter-catalog-list">
            <button
              v-for="chapter in chapters"
              :key="`drawer-${chapter.id}`"
              type="button"
              class="chapter-catalog-list__item"
              @click="handleChapterSelect(chapter.chapter_index)"
            >
              <span class="chapter-catalog-list__index">
                {{ formatChapterOrdinal(chapter.chapter_index) }}
              </span>
              <strong class="chapter-catalog-list__title">{{ chapter.chapter_title }}</strong>
              <span v-if="hasOffsets(chapter)" class="chapter-catalog-list__meta">
                范围 {{ formatNumber(chapter.start_offset) }} - {{ formatNumber(chapter.end_offset) }}
              </span>
            </button>
          </div>
        </div>
      </section>
    </n-drawer-content>
  </n-drawer>

  <n-modal
    v-else
    :show="show"
    preset="card"
    closable
    :mask-closable="true"
    :style="{ width: 'min(720px, calc(100vw - 32px))' }"
    @update:show="handleShowChange"
  >
    <template #header>
      <div class="chapter-catalog-panel__heading">
        <strong>目录</strong>
        <span class="chapter-catalog-panel__count">{{ chapterCountLabel }}</span>
      </div>
    </template>

    <section class="chapter-catalog-panel chapter-catalog-panel--modal">
      <div class="chapter-catalog-panel__summary">
        <p v-if="bookTitle" class="chapter-catalog-panel__book">{{ bookTitle }}</p>
        <p class="chapter-catalog-panel__hint">
          点击任意章节后会直接跳转到阅读页，并自动关闭目录面板。
        </p>
      </div>

      <div class="chapter-catalog-panel__body">
        <n-empty
          v-if="chapters.length === 0"
          description="当前还没有可展示的目录，请稍后再试或重新解析目录。"
          class="chapter-catalog-panel__empty"
        />

        <div v-else class="chapter-catalog-list">
          <button
            v-for="chapter in chapters"
            :key="`modal-${chapter.id}`"
            type="button"
            class="chapter-catalog-list__item"
            @click="handleChapterSelect(chapter.chapter_index)"
          >
            <span class="chapter-catalog-list__index">
              {{ formatChapterOrdinal(chapter.chapter_index) }}
            </span>
            <strong class="chapter-catalog-list__title">{{ chapter.chapter_title }}</strong>
            <span v-if="hasOffsets(chapter)" class="chapter-catalog-list__meta">
              范围 {{ formatNumber(chapter.start_offset) }} - {{ formatNumber(chapter.end_offset) }}
            </span>
          </button>
        </div>
      </div>
    </section>
  </n-modal>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { NDrawer, NDrawerContent, NEmpty, NModal } from "naive-ui";

import type { BookChapter, OnlineBookCatalogEntry } from "../types/api";
import { formatNumber } from "../utils/format";

const MOBILE_BREAKPOINT = 720;

const props = defineProps<{
  show: boolean;
  bookTitle: string;
  chapterCount: number;
  chapters: Array<BookChapter | OnlineBookCatalogEntry>;
}>();

const emit = defineEmits<{
  "update:show": [value: boolean];
  select: [chapterIndex: number];
}>();

const viewportWidth = ref(
  typeof window === "undefined" ? MOBILE_BREAKPOINT + 1 : window.innerWidth,
);

const isCompactViewport = computed(() => viewportWidth.value <= MOBILE_BREAKPOINT);
const drawerWidth = computed(() => Math.min(Math.max(viewportWidth.value, 320), 420));
const chapterCountLabel = computed(() => `共 ${formatNumber(props.chapterCount)} 章`);

onMounted(() => {
  syncViewportWidth();

  if (typeof window === "undefined") {
    return;
  }

  window.addEventListener("resize", handleWindowResize, { passive: true });
});

onUnmounted(() => {
  if (typeof window === "undefined") {
    return;
  }

  window.removeEventListener("resize", handleWindowResize);
});

function syncViewportWidth() {
  if (typeof window === "undefined") {
    return;
  }

  viewportWidth.value = window.innerWidth;
}

function handleWindowResize() {
  syncViewportWidth();
}

function handleShowChange(value: boolean) {
  emit("update:show", value);
}

function handleChapterSelect(chapterIndex: number) {
  emit("select", chapterIndex);
}

function formatChapterOrdinal(index: number) {
  return `第 ${formatNumber(index + 1)} 章`;
}

function hasOffsets(chapter: BookChapter | OnlineBookCatalogEntry) {
  return "start_offset" in chapter && "end_offset" in chapter;
}
</script>

<style scoped>
.chapter-catalog-panel {
  display: grid;
  gap: 18px;
}

.chapter-catalog-panel__summary {
  display: grid;
  gap: 10px;
  padding: 18px 20px;
  border: 1px solid rgba(109, 90, 74, 0.1);
  border-radius: 22px;
  background:
    radial-gradient(circle at top right, rgba(52, 107, 97, 0.16), transparent 34%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.92), rgba(244, 240, 233, 0.94));
}

.chapter-catalog-panel__heading {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.chapter-catalog-panel__heading strong {
  font-size: 22px;
}

.chapter-catalog-panel__count {
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 600;
}

.chapter-catalog-panel__book,
.chapter-catalog-panel__hint {
  margin: 0;
}

.chapter-catalog-panel__book {
  font-size: 16px;
  font-weight: 600;
  line-height: 1.6;
}

.chapter-catalog-panel__hint {
  color: var(--text-secondary);
  line-height: 1.7;
}

.chapter-catalog-panel__body {
  max-height: min(62vh, 560px);
  overflow: auto;
  padding-right: 4px;
}

.chapter-catalog-panel--drawer .chapter-catalog-panel__body {
  max-height: calc(100vh - 220px);
}

.chapter-catalog-panel__empty {
  padding: 28px 0;
}

.chapter-catalog-list {
  display: grid;
  gap: 10px;
}

.chapter-catalog-list__item {
  width: 100%;
  display: grid;
  gap: 6px;
  padding: 16px 18px;
  border: 1px solid rgba(109, 90, 74, 0.1);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.82);
  text-align: left;
  cursor: pointer;
  transition:
    transform 160ms ease,
    box-shadow 160ms ease,
    border-color 160ms ease,
    background 160ms ease;
}

.chapter-catalog-list__item:hover {
  transform: translateY(-1px);
  border-color: rgba(52, 107, 97, 0.28);
  box-shadow: 0 18px 30px rgba(82, 55, 28, 0.08);
  background: rgba(255, 255, 255, 0.94);
}

.chapter-catalog-list__item:focus-visible {
  outline: 2px solid color-mix(in srgb, var(--accent-color) 72%, white 28%);
  outline-offset: 2px;
}

.chapter-catalog-list__index,
.chapter-catalog-list__meta {
  color: var(--text-secondary);
  font-size: 13px;
}

.chapter-catalog-list__title {
  font-size: 16px;
  line-height: 1.65;
}

@media (max-width: 720px) {
  .chapter-catalog-panel__summary {
    padding: 16px 18px;
  }

  .chapter-catalog-panel__heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .chapter-catalog-panel__body {
    max-height: calc(100vh - 240px);
  }
}
</style>
