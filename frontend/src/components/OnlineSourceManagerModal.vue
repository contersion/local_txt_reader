<template>
  <n-modal
    :show="show"
    preset="card"
    :mask-closable="!submitting"
    :closable="!submitting"
    :style="modalStyle"
    @update:show="handleShowChange"
  >
    <template #header>
      <span>书源管理</span>
    </template>

    <div class="source-manager">
      <section class="source-manager__summary">
        <div class="source-manager__summary-head">
          <div>
            <strong>当前书源摘要</strong>
            <p>这里只做最小接入补丁。导入成功后会自动刷新这里的书源计数与摘要。</p>
          </div>

          <n-button
            quaternary
            size="small"
            :loading="summaryLoading"
            :disabled="submitting"
            @click="void loadSummary()"
          >
            刷新摘要
          </n-button>
        </div>

        <n-alert v-if="summaryError" type="warning" :show-icon="false">
          {{ summaryError }}
        </n-alert>

        <div class="source-manager__stats">
          <div class="source-manager__stat-card">
            <span>书源总数</span>
            <strong>{{ sources.length }}</strong>
          </div>
          <div class="source-manager__stat-card">
            <span>启用中</span>
            <strong>{{ enabledSourceCount }}</strong>
          </div>
          <div class="source-manager__stat-card">
            <span>校验有效</span>
            <strong>{{ validSourceCount }}</strong>
          </div>
        </div>

        <n-empty
          v-if="!summaryLoading && latestSources.length === 0"
          description="还没有已接入的书源。"
          size="small"
        />

        <div v-else class="source-manager__latest">
          <span class="source-manager__latest-label">最近书源</span>

          <div class="source-manager__latest-tags">
            <n-tag
              v-for="source in latestSources"
              :key="source.id"
              size="small"
              round
              :bordered="false"
              :type="source.validation_status === 'valid' ? 'success' : source.validation_status === 'invalid' ? 'error' : 'warning'"
            >
              {{ source.name }}
            </n-tag>
          </div>
        </div>
      </section>

      <n-alert
        v-if="importSuccessMessage"
        type="success"
        :show-icon="false"
        class="source-manager__feedback"
      >
        {{ importSuccessMessage }}
      </n-alert>

      <n-alert
        v-if="formErrorMessage"
        type="error"
        :show-icon="false"
        class="source-manager__feedback"
      >
        <div class="source-manager__issue-block">
          <strong>{{ formErrorMessage }}</strong>
          <span v-if="errorCodeText">错误码：{{ errorCodeText }}</span>
        </div>
      </n-alert>

      <n-alert
        v-if="warningCodeText"
        type="warning"
        :show-icon="false"
        class="source-manager__feedback"
      >
        <div class="source-manager__issue-block">
          <strong>导入结果包含 warning</strong>
          <span>warning：{{ warningCodeText }}</span>
        </div>
      </n-alert>

      <section v-if="step === 'menu'" class="source-manager__entry-panel">
        <div class="source-manager__panel-copy">
          <strong>选择接入方式</strong>
          <p>本轮只真实接通“粘贴 JSON”，其余入口先保留并统一提示暂未开放。</p>
        </div>

        <div class="source-manager__entry-grid">
          <button
            v-for="entry in entryOptions"
            :key="entry.key"
            type="button"
            class="source-manager__entry-button"
            @click="handleEntryClick(entry.key)"
          >
            <strong>{{ entry.label }}</strong>
            <span>{{ entry.description }}</span>
          </button>
        </div>
      </section>

      <section v-else class="source-manager__form-panel">
        <div class="source-manager__panel-copy">
          <strong>粘贴 Legado JSON</strong>
          <p>前端只做最小输入与错误展示，真实导入逻辑完全复用既有 Phase 2 后端契约。</p>
        </div>

        <n-input
          v-model:value="jsonText"
          type="textarea"
          :autosize="{ minRows: 10, maxRows: 18 }"
          :disabled="submitting"
          placeholder="请粘贴单条 Legado 书源 JSON 对象"
        />

        <div class="source-manager__hint">
          导入失败时会尽量展示后端返回的 `error_code`；warning 如有返回，也会在这里轻量展示。
        </div>

        <div class="source-manager__footer">
          <n-button :disabled="submitting" @click="backToMenu">
            返回
          </n-button>

          <n-space>
            <n-button :disabled="submitting" @click="closeModal">
              取消
            </n-button>
            <n-button
              type="primary"
              :loading="submitting"
              :disabled="!jsonText.trim()"
              @click="void handleImport()"
            >
              导入
            </n-button>
          </n-space>
        </div>
      </section>
    </div>
  </n-modal>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import {
  NAlert,
  NButton,
  NEmpty,
  NInput,
  NModal,
  NSpace,
  NTag,
  useMessage,
} from "naive-ui";

import { getErrorMessage } from "../api/client";
import {
  collectLegadoIssueCodes,
  getLegadoImportResultFromError,
  onlineSourcesApi,
} from "../api/online-sources";
import type { OnlineSourceSummary } from "../types/api";

type SourceManagerStep = "menu" | "json";
type SourceManagerEntryKey = "create" | "local" | "remote" | "json";

const props = defineProps<{
  show: boolean;
}>();

const emit = defineEmits<{
  (event: "update:show", value: boolean): void;
}>();

const message = useMessage();
const modalStyle = {
  width: "min(720px, calc(100vw - 24px))",
};

const entryOptions: Array<{ key: SourceManagerEntryKey; label: string; description: string }> = [
  {
    key: "create",
    label: "新建书源",
    description: "预留入口，本轮暂不开放。",
  },
  {
    key: "local",
    label: "本地导入",
    description: "预留入口，本轮暂不开放。",
  },
  {
    key: "remote",
    label: "网络导入",
    description: "预留入口，本轮暂不开放。",
  },
  {
    key: "json",
    label: "粘贴 JSON",
    description: "真实接通现有 Phase 2 导入接口。",
  },
];

const step = ref<SourceManagerStep>("menu");
const jsonText = ref("");
const submitting = ref(false);
const summaryLoading = ref(false);
const summaryError = ref<string | null>(null);
const formErrorMessage = ref<string | null>(null);
const importSuccessMessage = ref<string | null>(null);
const errorCodes = ref<string[]>([]);
const warningCodes = ref<string[]>([]);
const sources = ref<OnlineSourceSummary[]>([]);

const enabledSourceCount = computed(() => {
  return sources.value.filter((source) => source.enabled).length;
});

const validSourceCount = computed(() => {
  return sources.value.filter((source) => source.validation_status === "valid").length;
});

const latestSources = computed(() => {
  return [...sources.value]
    .sort((left, right) => Date.parse(right.updated_at) - Date.parse(left.updated_at))
    .slice(0, 4);
});

const errorCodeText = computed(() => errorCodes.value.join(" / "));
const warningCodeText = computed(() => warningCodes.value.join(" / "));

watch(
  () => props.show,
  (show) => {
    if (!show) {
      resetTransientState();
      return;
    }

    resetTransientState();
    void loadSummary();
  },
);

function handleShowChange(value: boolean) {
  emit("update:show", value);
}

function closeModal() {
  if (submitting.value) {
    return;
  }

  emit("update:show", false);
}

function resetTransientState() {
  step.value = "menu";
  jsonText.value = "";
  formErrorMessage.value = null;
  importSuccessMessage.value = null;
  errorCodes.value = [];
  warningCodes.value = [];
}

function resetImportFeedback() {
  formErrorMessage.value = null;
  importSuccessMessage.value = null;
  errorCodes.value = [];
  warningCodes.value = [];
}

async function loadSummary() {
  summaryLoading.value = true;
  summaryError.value = null;

  try {
    sources.value = await onlineSourcesApi.list();
  } catch (error) {
    sources.value = [];
    summaryError.value = getErrorMessage(error);
  } finally {
    summaryLoading.value = false;
  }
}

function handleEntryClick(entryKey: SourceManagerEntryKey) {
  resetImportFeedback();

  if (entryKey !== "json") {
    message.info("暂未开放");
    return;
  }

  step.value = "json";
}

function backToMenu() {
  if (submitting.value) {
    return;
  }

  resetImportFeedback();
  step.value = "menu";
}

function parseJsonSource() {
  const rawText = jsonText.value.trim();

  if (!rawText) {
    throw new Error("请先粘贴要导入的 JSON 内容。");
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(rawText);
  } catch (error) {
    throw new Error(`JSON 格式无效：${error instanceof Error ? error.message : "无法解析"}`);
  }

  if (Array.isArray(parsed) || typeof parsed !== "object" || parsed === null) {
    throw new Error("当前仅支持粘贴单条书源 JSON 对象。");
  }

  return parsed as Record<string, unknown>;
}

async function handleImport() {
  resetImportFeedback();

  let sourcePayload: Record<string, unknown>;
  try {
    sourcePayload = parseJsonSource();
  } catch (error) {
    formErrorMessage.value = getErrorMessage(error);
    message.error(formErrorMessage.value);
    return;
  }

  submitting.value = true;

  try {
    const result = await onlineSourcesApi.importLegado(sourcePayload);
    warningCodes.value = collectLegadoIssueCodes(result.warnings);

    const importedName = result.mapped_source?.name || "书源";
    const suffix = result.source_id ? `（ID: ${result.source_id}）` : "";
    importSuccessMessage.value = `已成功导入“${importedName}”${suffix}`;
    message.success(`书源导入成功：${importedName}`);

    if (warningCodes.value.length > 0) {
      message.warning(`导入成功，但包含 warning：${warningCodes.value.join(" / ")}`);
    }

    jsonText.value = "";
    await loadSummary();
  } catch (error) {
    const importResult = getLegadoImportResultFromError(error);

    if (importResult) {
      errorCodes.value = collectLegadoIssueCodes(importResult.errors);
      warningCodes.value = collectLegadoIssueCodes(importResult.warnings);

      const firstMessage = importResult.errors[0]?.message || getErrorMessage(error);
      formErrorMessage.value = firstMessage;

      message.error(
        errorCodes.value.length > 0
          ? `导入失败：${errorCodes.value.join(" / ")}`
          : firstMessage,
      );
    } else {
      formErrorMessage.value = getErrorMessage(error);
      message.error(formErrorMessage.value);
    }
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
.source-manager {
  display: grid;
  gap: 16px;
}

.source-manager__summary,
.source-manager__entry-panel,
.source-manager__form-panel {
  display: grid;
  gap: 16px;
  padding: 16px 18px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.58);
}

.source-manager__summary-head,
.source-manager__footer {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.source-manager__summary-head p,
.source-manager__panel-copy p,
.source-manager__hint {
  margin: 8px 0 0;
  color: var(--text-secondary);
  line-height: 1.7;
}

.source-manager__panel-copy strong,
.source-manager__summary-head strong {
  display: block;
  font-size: 16px;
}

.source-manager__stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.source-manager__stat-card {
  padding: 14px 16px;
  border: 1px solid var(--border-color-soft);
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.76);
}

.source-manager__stat-card span {
  display: block;
  color: var(--text-secondary);
  font-size: 12px;
}

.source-manager__stat-card strong {
  display: block;
  margin-top: 6px;
  font-size: 22px;
  line-height: 1.1;
}

.source-manager__latest {
  display: grid;
  gap: 10px;
}

.source-manager__latest-label {
  color: var(--text-secondary);
  font-size: 12px;
}

.source-manager__latest-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.source-manager__feedback {
  border-radius: 16px;
}

.source-manager__issue-block {
  display: grid;
  gap: 6px;
}

.source-manager__entry-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.source-manager__entry-button {
  min-width: 0;
  display: grid;
  gap: 8px;
  padding: 16px;
  border: 1px solid var(--border-color-soft);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.78);
  color: var(--text-primary);
  text-align: left;
  cursor: pointer;
  transition:
    border-color 180ms ease,
    box-shadow 180ms ease,
    transform 180ms ease;
}

.source-manager__entry-button:hover {
  transform: translateY(-1px);
  border-color: rgba(184, 93, 54, 0.18);
  box-shadow: var(--shadow-soft);
}

.source-manager__entry-button strong {
  font-size: 15px;
  line-height: 1.4;
}

.source-manager__entry-button span {
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.7;
}

@media (max-width: 720px) {
  .source-manager__summary,
  .source-manager__entry-panel,
  .source-manager__form-panel {
    padding: 14px;
  }

  .source-manager__summary-head,
  .source-manager__footer {
    flex-direction: column;
    align-items: stretch;
  }

  .source-manager__stats,
  .source-manager__entry-grid {
    grid-template-columns: 1fr;
  }
}
</style>
