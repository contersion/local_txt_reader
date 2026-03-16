<template>
  <div class="rule-page">
    <section class="rule-page__intro-stack">
      <section class="rule-page__hero">
        <div class="rule-page__hero-copy">
          <div class="rule-page__eyebrow">Chapter Rules</div>
          <h1 class="rule-page__title">把章节识别规则做成真正可管理、可验证的资产。</h1>
          <p class="rule-page__description">
            这里统一管理内置规则和你的自定义规则。你可以新增、编辑、删除自定义规则，快速切换默认规则，并直接在页面里验证规则是否真的匹配预期章节。
          </p>
        </div>

        <div class="rule-page__hero-aside">
          <div class="rule-page__stats">
            <div class="rule-page__stat">
              <span>规则总数</span>
              <strong>{{ rules.length }}</strong>
            </div>
            <div class="rule-page__stat">
              <span>内置规则</span>
              <strong>{{ builtInRules.length }}</strong>
            </div>
            <div class="rule-page__stat">
              <span>自定义规则</span>
              <strong>{{ customRules.length }}</strong>
            </div>
          </div>
        </div>
      </section>

      <section class="rule-page__toolbar">
        <div class="rule-page__toolbar-note">
          <span>当前默认规则</span>
          <strong>{{ defaultRuleName }}</strong>
        </div>

        <div class="rule-page__toolbar-actions">
          <n-button secondary :loading="loading" @click="loadInitialData">刷新页面</n-button>
          <n-button type="primary" @click="openCreateModal">新增自定义规则</n-button>
        </div>
      </section>
    </section>

    <n-alert v-if="pageError" type="error" :show-icon="false" class="rule-page__alert">
      {{ pageError }}
    </n-alert>

    <n-card :bordered="false" class="rule-page__table-card">
      <template #header>
        <span class="rule-page__card-title">规则列表</span>
      </template>
      <template #header-extra>
        <span class="rule-page__card-subtitle">表格 + 弹窗表单</span>
      </template>

      <n-empty v-if="!loading && rules.length === 0" description="还没有可展示的规则。" />

      <div v-else-if="isMobileViewport" class="rule-mobile-list" aria-label="规则卡片列表">
        <article
          v-for="rule in rules"
          :key="`mobile-rule-${rule.id}`"
          class="rule-mobile-card"
        >
          <div class="rule-mobile-card__header">
            <div class="rule-mobile-card__title-block">
              <strong class="rule-mobile-card__title">{{ rule.rule_name }}</strong>
              <span class="rule-mobile-card__time">{{ formatDate(rule.updated_at) }}</span>
            </div>

            <div class="rule-mobile-card__badges">
              <n-tag size="small" round :bordered="false" :type="rule.is_builtin ? 'warning' : 'info'">
                {{ rule.is_builtin ? "内置" : "自定义" }}
              </n-tag>
              <n-tag v-if="rule.is_default" size="small" round :bordered="false" type="success">
                当前默认
              </n-tag>
            </div>
          </div>

          <div class="rule-mobile-card__section">
            <span class="rule-mobile-card__label">Regex</span>
            <code class="rule-code-block">{{ rule.regex_pattern }}</code>
          </div>

          <div class="rule-mobile-card__meta">
            <div class="rule-mobile-card__section">
              <span class="rule-mobile-card__label">Flags</span>
              <span class="rule-mobile-card__value">{{ rule.flags || "无 flags" }}</span>
            </div>
            <div class="rule-mobile-card__section">
              <span class="rule-mobile-card__label">说明</span>
              <p class="rule-mobile-card__description">{{ rule.description || "暂无说明" }}</p>
            </div>
          </div>

          <div class="rule-mobile-card__actions">
            <n-button block secondary @click="loadRuleIntoTest(rule)">带入测试</n-button>
            <n-button block tertiary @click="loadRuleIntoApply(rule)">应用到书</n-button>
            <n-button
              block
              :secondary="!rule.is_default"
              :type="rule.is_default ? 'success' : 'primary'"
              :disabled="rule.is_default"
              @click="() => { void handleSetDefault(rule); }"
            >
              {{ rule.is_default ? "默认中" : "设为默认" }}
            </n-button>
            <n-button v-if="!rule.is_builtin" block tertiary @click="openEditModal(rule)">编辑</n-button>
            <n-popconfirm v-if="!rule.is_builtin" @positive-click="() => { void handleDelete(rule); }">
              <template #trigger>
                <n-button block tertiary type="error">删除</n-button>
              </template>
              删除后无法恢复，确认继续吗？
            </n-popconfirm>
          </div>
        </article>
      </div>

      <div v-else class="rule-page__table-wrap">
        <n-data-table
          :columns="columns"
          :data="rules"
          :loading="loading"
          :row-key="rowKey"
          :single-line="false"
          :pagination="pagination"
          size="small"
        />
      </div>
    </n-card>

    <n-card :bordered="false" class="rule-page__apply-card">
      <template #header>
        <span class="rule-page__card-title">将规则应用到书籍</span>
      </template>
      <template #header-extra>
        <span class="rule-page__card-subtitle">快速重解析目录</span>
      </template>

      <div class="rule-apply">
        <section class="rule-apply__form">
          <div class="rule-apply__lead">
            <strong>把一条规则直接应用到某本书</strong>
            <p>你可以从上方规则表点击“应用到书”，也可以在这里手动选择规则和目标书籍，然后立即触发重新解析。</p>
          </div>

          <n-form label-placement="top">
            <n-form-item label="当前应用规则">
              <n-input
                :value="currentApplyRuleName || '未指定，请先选择一条规则'"
                readonly
              />
            </n-form-item>

            <n-form-item label="目录规则">
              <n-select
                v-model:value="quickApplyState.rule_id"
                :options="ruleOptions"
                :loading="loading"
                :disabled="loading || ruleOptions.length === 0 || applyPending"
                placeholder="选择要应用的目录规则"
                @update:value="clearApplyResult"
              />
              <div class="rule-field__hint">
                <span>建议先在下方测试区验证命中效果，再应用到真实书籍。</span>
              </div>
            </n-form-item>

            <n-form-item label="目标书籍">
              <n-select
                v-model:value="quickApplyState.book_id"
                :options="bookOptions"
                :loading="booksLoading"
                :disabled="booksLoading || bookOptions.length === 0 || applyPending"
                placeholder="选择要重新解析目录的书"
                @update:value="clearApplyResult"
              />
            </n-form-item>

            <div class="rule-apply__actions">
              <n-button type="primary" :loading="applyPending" @click="runQuickApply">
                应用规则并重解析
              </n-button>
              <n-button secondary :disabled="applyPending" @click="clearApplyResult">
                清空结果
              </n-button>
            </div>
          </n-form>
        </section>

        <section class="rule-apply__result">
          <n-alert
            v-if="booksError"
            type="warning"
            :show-icon="false"
            class="rule-test__alert"
          >
            {{ booksError }}
          </n-alert>

          <n-alert
            v-if="applyErrorMessage"
            type="error"
            :show-icon="false"
            class="rule-test__alert"
          >
            {{ applyErrorMessage }}
          </n-alert>

          <template v-if="applyResult">
            <div class="rule-apply__summary">
              <div class="rule-apply__summary-card">
                <span>书籍</span>
                <strong>{{ applyResultBookTitle }}</strong>
              </div>
              <div class="rule-apply__summary-card">
                <span>规则</span>
                <strong>{{ applyResultRuleName }}</strong>
              </div>
              <div class="rule-apply__summary-card">
                <span>总章节</span>
                <strong>{{ applyResult.total_chapters }}</strong>
              </div>
            </div>

            <n-empty
              v-if="applyResult.chapters.length === 0"
              description="这次重解析没有识别出目录，可先回到测试区继续调整规则。"
              class="rule-test__empty"
            />

            <template v-else>
              <div v-if="isMobileViewport" class="rule-mobile-result-list">
                <article
                  v-for="chapter in applyPreviewChapters"
                  :key="`${chapter.chapter_index}-${chapter.start_offset}`"
                  class="rule-mobile-result-card"
                >
                  <div class="rule-mobile-result-card__row">
                    <span>chapter_index</span>
                    <strong>{{ chapter.chapter_index }}</strong>
                  </div>
                  <div class="rule-mobile-result-card__block">
                    <span>chapter_title</span>
                    <code class="rule-code-block">{{ chapter.chapter_title }}</code>
                  </div>
                  <div class="rule-mobile-result-card__row">
                    <span>offset</span>
                    <strong>{{ chapter.start_offset }} - {{ chapter.end_offset }}</strong>
                  </div>
                </article>
              </div>

              <div v-else class="rule-apply__table-wrap">
                <n-table striped :single-line="false">
                  <thead>
                    <tr>
                      <th>chapter_index</th>
                      <th>chapter_title</th>
                      <th>offset</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="chapter in applyPreviewChapters"
                      :key="`${chapter.chapter_index}-${chapter.start_offset}`"
                    >
                      <td>{{ chapter.chapter_index }}</td>
                      <td class="rule-test__match-cell">{{ chapter.chapter_title }}</td>
                      <td>{{ chapter.start_offset }} - {{ chapter.end_offset }}</td>
                    </tr>
                  </tbody>
                </n-table>
              </div>
              <p class="rule-apply__note">
                当前展示前 {{ applyPreviewChapters.length }} 条目录预览，完整目录可到书籍详情页继续查看。              </p>
            </template>
          </template>

          <div v-else class="rule-apply__placeholder">
            <strong>这里会显示应用结果</strong>
            <p>成功后会返回重新解析后的章节数和目录预览，便于你马上判断这条规则是否适合这本书。</p>
          </div>
        </section>
      </div>
    </n-card>

    <n-card :bordered="false" class="rule-page__test-card">
      <template #header>
        <span class="rule-page__card-title">规则测试与预览</span>
      </template>
      <template #header-extra>
        <span class="rule-page__card-subtitle">{{ testModeLabel }}</span>
      </template>

      <div class="rule-test">
        <section class="rule-test__form">
          <div class="rule-test__lead">
            <strong>测试当前规则</strong>
            <p>先把某条规则带入测试区，再选择“书籍测试”或“原始文本片段测试”。</p>
          </div>

          <n-form label-placement="top">
            <n-form-item label="当前测试规则">
              <n-input
                :value="testState.loadedRuleName || '未指定，支持直接手动输入'"
                readonly
              />
            </n-form-item>

            <n-form-item label="regex_pattern">
              <n-input
                v-model:value="testState.regex_pattern"
                type="textarea"
                :autosize="{ minRows: 4, maxRows: 8 }"
                placeholder="例如：^\s*第\s*\d+\s*[章节回].*$"
              />
              <div class="rule-field__hint">
                <span>示例提示：</span>
                <n-space size="small" wrap>
                  <n-button
                    v-for="example in regexExamples"
                    :key="example.label"
                    size="tiny"
                    tertiary
                    @click="applyExampleToTest(example)"
                  >
                    {{ example.label }}
                  </n-button>
                </n-space>
              </div>
            </n-form-item>

            <n-form-item label="Flags">
              <n-input
                v-model:value="testState.flags"
                placeholder="例如：MULTILINE 或 IGNORECASE|MULTILINE"
              />
            </n-form-item>

            <n-form-item label="测试方式">
              <n-radio-group v-model:value="testState.mode">
                <n-space wrap>
                  <n-radio-button value="book">选择一本已上传的书</n-radio-button>
                  <n-radio-button value="text">输入原始文本片段</n-radio-button>
                </n-space>
              </n-radio-group>
            </n-form-item>

            <n-form-item v-if="testState.mode === 'book'" label="测试书籍">
              <n-select
                v-model:value="testState.book_id"
                :options="bookOptions"
                :loading="booksLoading"
                :disabled="booksLoading || bookOptions.length === 0"
                placeholder="选择一本已上传的书"
              />
              <div class="rule-field__hint">
                <span>适合验证“整本书真实目录是否能被匹配出来”。</span>
              </div>
            </n-form-item>

            <n-form-item v-else label="原始文本片段">
              <n-input
                v-model:value="testState.text"
                type="textarea"
                :autosize="{ minRows: 8, maxRows: 14 }"
                placeholder="粘贴一段章节标题附近的原始文本，例如：&#10;第1章 初始之夜&#10;风吹过旧城区……"
              />
              <div class="rule-field__hint">
                <span>适合快速验证某个标题样式是否能命中，不必依赖整本书。</span>
              </div>
            </n-form-item>

            <div class="rule-test__actions">
              <n-button type="primary" :loading="testPending" @click="runRuleTest">
                开始测试              </n-button>
              <n-button secondary :disabled="testPending" @click="clearTestResult">
                清空结果
              </n-button>
            </div>
          </n-form>
        </section>

        <section class="rule-test__result">
          <n-alert
            v-if="booksError"
            type="warning"
            :show-icon="false"
            class="rule-test__alert"
          >
            {{ booksError }}
          </n-alert>

          <n-alert
            v-if="testErrorMessage"
            type="error"
            :show-icon="false"
            class="rule-test__alert"
          >
            {{ testErrorMessage }}
          </n-alert>

          <template v-if="testResult">
            <div class="rule-test__summary">
              <div class="rule-test__summary-card">
                <span>matched</span>
                <strong>{{ testResult.matched ? "true" : "false" }}</strong>
              </div>
              <div class="rule-test__summary-card">
                <span>count</span>
                <strong>{{ testResult.count }}</strong>
              </div>
              <div class="rule-test__summary-card">
                <span>来源</span>
                <strong>{{ testModeLabel }}</strong>
              </div>
            </div>

            <n-empty
              v-if="testResult.items.length === 0"
              description="这次测试没有找到匹配项，可以调整正则或 flags 后再试。"
              class="rule-test__empty"
            />

            <div v-else-if="isMobileViewport" class="rule-mobile-result-list">
              <article
                v-for="(item, index) in testResult.items"
                :key="`${item.start}-${item.end}-${index}`"
                class="rule-mobile-result-card"
              >
                <div class="rule-mobile-result-card__block">
                  <span>匹配文本</span>
                  <code class="rule-code-block">{{ item.text }}</code>
                </div>
                <div class="rule-mobile-result-card__row">
                  <span>start</span>
                  <strong>{{ item.start }}</strong>
                </div>
                <div class="rule-mobile-result-card__row">
                  <span>end</span>
                  <strong>{{ item.end }}</strong>
                </div>
              </article>
            </div>

            <div v-else class="rule-test__table-wrap">
              <n-table striped :single-line="false">
                <thead>
                  <tr>
                    <th>匹配文本</th>
                    <th>start</th>
                    <th>end</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, index) in testResult.items" :key="`${item.start}-${item.end}-${index}`">
                    <td class="rule-test__match-cell">{{ item.text }}</td>
                    <td>{{ item.start }}</td>
                    <td>{{ item.end }}</td>
                  </tr>
                </tbody>
              </n-table>
            </div>
          </template>

          <div v-else class="rule-test__placeholder">
            <strong>这里会显示测试结果</strong>
            <p>你可以先从上面的规则列表里点击“带入测试”，也可以直接手动输入 regex 与 flags。</p>
          </div>
        </section>
      </div>
    </n-card>

    <n-modal
      v-model:show="modalVisible"
      preset="card"
      :mask-closable="!submitting"
      :closable="!submitting"
      :style="modalStyle"
    >
      <template #header>
        <span>{{ modalTitle }}</span>
      </template>

      <div class="rule-form__intro">
        <p>自定义规则支持常见正则 flags，例如 <code>IGNORECASE|MULTILINE</code>。</p>
      </div>

      <n-form label-placement="top">
        <n-form-item label="规则名称">
          <n-input
            v-model:value="formModel.rule_name"
            maxlength="100"
            placeholder="例如：轻小说章节规则"
          />
        </n-form-item>

        <n-form-item label="正则表达式">
          <n-input
            v-model:value="formModel.regex_pattern"
            type="textarea"
            :autosize="{ minRows: 4, maxRows: 8 }"
            placeholder="例如：^\s*第\s*\d+\s*[章节回].*$"
          />
          <div class="rule-field__hint">
            <span>示例提示：</span>
            <n-space size="small" wrap>
              <n-button
                v-for="example in regexExamples"
                :key="`form-${example.label}`"
                size="tiny"
                tertiary
                @click="applyExampleToForm(example)"
              >
                {{ example.label }}
              </n-button>
            </n-space>
          </div>
        </n-form-item>

        <n-form-item label="Flags">
          <n-input
            v-model:value="formModel.flags"
            placeholder="例如：MULTILINE 或 IGNORECASE|MULTILINE"
          />
        </n-form-item>

        <n-form-item label="说明">
          <n-input
            v-model:value="formModel.description"
            type="textarea"
            :autosize="{ minRows: 3, maxRows: 6 }"
            placeholder="简要说明这个规则适合匹配什么样的章节标题"
          />
        </n-form-item>

        <n-form-item>
          <n-checkbox v-model:checked="formModel.is_default">保存后设为默认规则</n-checkbox>
        </n-form-item>
      </n-form>

      <template #footer>
        <div class="rule-form__footer">
          <n-button :disabled="submitting" @click="closeModal">取消</n-button>
          <n-button type="primary" :loading="submitting" @click="submitForm">保存规则</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, h, onMounted, onUnmounted, reactive, ref } from "vue";
import {
  NAlert,
  NButton,
  NCard,
  NCheckbox,
  NDataTable,
  NEmpty,
  NForm,
  NFormItem,
  NInput,
  NModal,
  NPopconfirm,
  NRadioButton,
  NRadioGroup,
  NSpace,
  NSelect,
  NTable,
  NTag,
  useMessage,
  type DataTableColumns,
  type PaginationProps,
} from "naive-ui";

import { booksApi } from "../api/books";
import { chapterRulesApi } from "../api/chapter-rules";
import { getErrorMessage } from "../api/client";
import type {
  BookReparseResponse,
  BookShelfItem,
  ChapterRule,
  ChapterRuleTestResponse,
} from "../types/api";

interface RuleFormModel {
  rule_name: string;
  regex_pattern: string;
  flags: string;
  description: string;
  is_default: boolean;
}

interface RegexExample {
  label: string;
  pattern: string;
  flags: string;
}

interface RuleTestState {
  mode: "book" | "text";
  book_id: number | null;
  text: string;
  regex_pattern: string;
  flags: string;
  loadedRuleName: string | null;
}

interface QuickApplyState {
  rule_id: number | null;
  book_id: number | null;
}

const MOBILE_BREAKPOINT = 720;

const regexExamples: RegexExample[] = [
  {
    label: "中文章节",
    pattern: "^\\s*第\\s*[0-9零〇一二两三四五六七八九十百千万]+\\s*[章节回篇]\\s*.*$",
    flags: "MULTILINE",
  },
  {
    label: "英文章节",
    pattern: "^\\s*chapter\\s+\\d+\\s*.*$",
    flags: "IGNORECASE|MULTILINE",
  },
  {
    label: "卷章混合",
    pattern: "^\\s*第\\s*[0-9零〇一二两三四五六七八九十百千万]+\\s*卷\\s+第\\s*[0-9零〇一二两三四五六七八九十百千万]+\\s*[章节回]\\s*.*$",
    flags: "MULTILINE",
  },
];

const message = useMessage();
const rules = ref<ChapterRule[]>([]);
const books = ref<BookShelfItem[]>([]);
const loading = ref(false);
const booksLoading = ref(false);
const submitting = ref(false);
const testPending = ref(false);
const applyPending = ref(false);
const viewportWidth = ref(typeof window === "undefined" ? MOBILE_BREAKPOINT + 1 : window.innerWidth);
const pageError = ref<string | null>(null);
const booksError = ref<string | null>(null);
const testErrorMessage = ref<string | null>(null);
const applyErrorMessage = ref<string | null>(null);
const testResult = ref<ChapterRuleTestResponse | null>(null);
const applyResult = ref<BookReparseResponse | null>(null);
const modalVisible = ref(false);
const editingRuleId = ref<number | null>(null);
const formModel = reactive<RuleFormModel>(createEmptyForm());
const testState = reactive<RuleTestState>({
  mode: "book",
  book_id: null,
  text: "",
  regex_pattern: "",
  flags: "",
  loadedRuleName: null,
});
const quickApplyState = reactive<QuickApplyState>({
  rule_id: null,
  book_id: null,
});

const pagination: PaginationProps = {
  pageSize: 8,
};

const modalStyle = {
  width: "min(760px, calc(100vw - 24px))",
};

const builtInRules = computed(() => rules.value.filter((rule) => rule.is_builtin));
const customRules = computed(() => rules.value.filter((rule) => !rule.is_builtin));
const defaultRuleName = computed(() => {
  return rules.value.find((rule) => rule.is_default)?.rule_name || "未设置";
});
const modalTitle = computed(() => {
  return editingRuleId.value ? "编辑自定义规则" : "新增自定义规则";
});
const bookOptions = computed(() => {
  return books.value.map((book) => ({
    label: book.title,
    value: book.id,
  }));
});
const ruleOptions = computed(() => {
  return rules.value.map((rule) => ({
    label: rule.is_default ? `${rule.rule_name} · 当前默认` : rule.rule_name,
    value: rule.id,
  }));
});
const testModeLabel = computed(() => {
  return testState.mode === "book" ? "书籍测试" : "原始文本片段测试";
});
const currentApplyRuleName = computed(() => {
  return rules.value.find((rule) => rule.id === quickApplyState.rule_id)?.rule_name || "";
});
const applyResultBookTitle = computed(() => {
  return books.value.find((book) => book.id === applyResult.value?.book_id)?.title || "目标书籍";
});
const applyResultRuleName = computed(() => {
  return rules.value.find((rule) => rule.id === applyResult.value?.chapter_rule_id)?.rule_name || "目录规则";
});
const applyPreviewChapters = computed(() => {
  return (applyResult.value?.chapters || []).slice(0, 6);
});
const isMobileViewport = computed(() => viewportWidth.value <= MOBILE_BREAKPOINT);

function createEmptyForm(): RuleFormModel {
  return {
    rule_name: "",
    regex_pattern: "",
    flags: "",
    description: "",
    is_default: false,
  };
}

function resetForm() {
  Object.assign(formModel, createEmptyForm());
}

function rowKey(row: ChapterRule) {
  return row.id;
}

function getFallbackRule() {
  return rules.value.find((rule) => rule.is_default) || rules.value[0] || null;
}

function formatDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "时间未知";
  }

  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function handleWindowResize() {
  if (typeof window === "undefined") {
    return;
  }

  viewportWidth.value = window.innerWidth;
}

function applyExampleToForm(example: RegexExample) {
  formModel.regex_pattern = example.pattern;
  formModel.flags = example.flags;
}

function applyExampleToTest(example: RegexExample) {
  testState.regex_pattern = example.pattern;
  testState.flags = example.flags;
  testState.loadedRuleName = `${example.label} 示例`;
  clearTestResult();
}

function loadRuleIntoTest(rule: ChapterRule, shouldNotify = true) {
  testState.regex_pattern = rule.regex_pattern;
  testState.flags = rule.flags;
  testState.loadedRuleName = rule.rule_name;
  clearTestResult();

  if (shouldNotify) {
    message.success(`已将“${rule.rule_name}”带入测试区`);
  }
}

function loadRuleIntoApply(rule: ChapterRule, shouldNotify = true) {
  quickApplyState.rule_id = rule.id;
  clearApplyResult();

  if (shouldNotify) {
    message.success(`已选中“${rule.rule_name}”，现在可以直接应用到书籍`);
  }
}

function hydrateDefaultRuleToTest() {
  if (testState.regex_pattern.trim()) {
    return;
  }

  const fallbackRule = getFallbackRule();
  if (!fallbackRule) {
    return;
  }

  loadRuleIntoTest(fallbackRule, false);
}

function hydrateDefaultRuleToApply() {
  if (quickApplyState.rule_id && rules.value.some((rule) => rule.id === quickApplyState.rule_id)) {
    return;
  }

  const fallbackRule = getFallbackRule();
  if (!fallbackRule) {
    quickApplyState.rule_id = null;
    return;
  }

  loadRuleIntoApply(fallbackRule, false);
}

function openCreateModal() {
  editingRuleId.value = null;
  resetForm();
  modalVisible.value = true;
}

function openEditModal(rule: ChapterRule) {
  editingRuleId.value = rule.id;
  Object.assign(formModel, {
    rule_name: rule.rule_name,
    regex_pattern: rule.regex_pattern,
    flags: rule.flags,
    description: rule.description || "",
    is_default: rule.is_default,
  });
  modalVisible.value = true;
}

function closeModal() {
  if (submitting.value) {
    return;
  }

  modalVisible.value = false;
  editingRuleId.value = null;
  resetForm();
}

async function loadRules() {
  loading.value = true;
  pageError.value = null;

  try {
    rules.value = await chapterRulesApi.list();
    hydrateDefaultRuleToTest();
    hydrateDefaultRuleToApply();
  } catch (error) {
    rules.value = [];
    pageError.value = getErrorMessage(error);
  } finally {
    loading.value = false;
  }
}

async function loadBooks() {
  booksLoading.value = true;
  booksError.value = null;

  try {
    books.value = await booksApi.list();

    const firstBookId = books.value[0]?.id ?? null;
    const hasTestBook = !!books.value.find((book) => book.id === testState.book_id);
    const hasApplyBook = !!books.value.find((book) => book.id === quickApplyState.book_id);

    if (!hasTestBook) {
      testState.book_id = firstBookId;
    }

    if (!hasApplyBook) {
      quickApplyState.book_id = firstBookId;
    }
  } catch (error) {
    books.value = [];
    booksError.value = getErrorMessage(error);
  } finally {
    booksLoading.value = false;
  }
}

async function loadInitialData() {
  await Promise.all([loadRules(), loadBooks()]);
}

async function submitForm() {
  const ruleName = formModel.rule_name.trim();
  const regexPattern = formModel.regex_pattern.trim();

  if (!ruleName) {
    message.warning("请先填写规则名称");
    return;
  }

  if (!regexPattern) {
    message.warning("请先填写正则表达式");
    return;
  }

  submitting.value = true;

  try {
    const payload = {
      rule_name: ruleName,
      regex_pattern: regexPattern,
      flags: formModel.flags.trim(),
      description: formModel.description.trim() || null,
      is_default: formModel.is_default,
    };

    if (editingRuleId.value) {
      await chapterRulesApi.update(editingRuleId.value, payload);
      message.success("规则已更新");
    } else {
      await chapterRulesApi.create(payload);
      message.success("规则已创建");
    }

    closeModal();
    await loadRules();
  } catch (error) {
    message.error(getErrorMessage(error));
  } finally {
    submitting.value = false;
  }
}

async function handleSetDefault(rule: ChapterRule) {
  if (rule.is_default) {
    return;
  }

  try {
    await chapterRulesApi.update(rule.id, { is_default: true });
    message.success(`已将“${rule.rule_name}”设为默认规则`);
    await loadRules();
  } catch (error) {
    message.error(getErrorMessage(error));
  }
}

async function handleDelete(rule: ChapterRule) {
  try {
    await chapterRulesApi.remove(rule.id);
    message.success(`已删除“${rule.rule_name}”`);
    await loadRules();
  } catch (error) {
    message.error(getErrorMessage(error));
  }
}

function clearTestResult() {
  testResult.value = null;
  testErrorMessage.value = null;
}

function clearApplyResult() {
  applyResult.value = null;
  applyErrorMessage.value = null;
}

function getFriendlyTestError(error: unknown) {
  const raw = getErrorMessage(error);
  const normalized = raw.toLowerCase();

  if (raw.includes("Either book_id or text is required")) {
    return "请选择一本书或输入一段原始文本后再开始测试。";
  }

  if (normalized.includes("regex") || normalized.includes("pattern") || normalized.includes("unterminated") || normalized.includes("nothing to repeat") || normalized.includes("bad escape") || normalized.includes("missing")) {
    return `正则表达式有误：${raw}`;
  }

  if (normalized.includes("book not found")) {
    return "找不到你选中的书籍，请刷新列表后重试。";
  }

  return raw;
}

function getFriendlyApplyError(error: unknown) {
  const raw = getErrorMessage(error);
  const normalized = raw.toLowerCase();

  if (normalized.includes("book not found")) {
    return "找不到你选中的书籍，请刷新书架列表后重试。";
  }

  if (normalized.includes("rule not found") || normalized.includes("chapter rule")) {
    return "找不到你选中的目录规则，请刷新规则列表后重试。";
  }

  return raw;
}

async function runRuleTest() {
  clearTestResult();

  const regexPattern = testState.regex_pattern.trim();
  const flags = testState.flags.trim();

  if (!regexPattern) {
    testErrorMessage.value = "请先输入要测试的正则表达式。";
    return;
  }

  if (testState.mode === "book" && !testState.book_id) {
    testErrorMessage.value = "请先选择一本已上传的书。";
    return;
  }

  if (testState.mode === "text" && !testState.text.trim()) {
    testErrorMessage.value = "请先输入原始文本片段。";
    return;
  }

  testPending.value = true;

  try {
    testResult.value = await chapterRulesApi.test(
      testState.mode === "book"
        ? {
            book_id: testState.book_id || undefined,
            regex_pattern: regexPattern,
            flags,
          }
        : {
            text: testState.text.trim(),
            regex_pattern: regexPattern,
            flags,
          },
    );

    message.success("规则测试已完成");
  } catch (error) {
    testErrorMessage.value = getFriendlyTestError(error);
  } finally {
    testPending.value = false;
  }
}

async function runQuickApply() {
  clearApplyResult();

  if (!quickApplyState.rule_id) {
    applyErrorMessage.value = "请先选择要应用的目录规则。";
    return;
  }

  if (!quickApplyState.book_id) {
    applyErrorMessage.value = "请先选择一本要重新解析目录的书。";
    return;
  }

  applyPending.value = true;

  try {
    applyResult.value = await booksApi.reparse(quickApplyState.book_id, quickApplyState.rule_id);

    const bookTitle = books.value.find((book) => book.id === quickApplyState.book_id)?.title || "目标书籍";
    const ruleName = rules.value.find((rule) => rule.id === quickApplyState.rule_id)?.rule_name || "目录规则";

    message.success(`已将“${ruleName}”应用到《${bookTitle}》，共识别 ${applyResult.value.total_chapters} 个章节`);
  } catch (error) {
    applyErrorMessage.value = getFriendlyApplyError(error);
  } finally {
    applyPending.value = false;
  }
}

const columns = computed<DataTableColumns<ChapterRule>>(() => [
  {
    title: "规则信息",
    key: "rule_name",
    minWidth: 220,
    render: (row) => h("div", { class: "rule-table__primary" }, [
      h("strong", { class: "rule-table__title" }, row.rule_name),
      h("div", { class: "rule-table__badges" }, [
        h(NTag, {
          size: "small",
          round: true,
          bordered: false,
          type: row.is_builtin ? "warning" : "info",
        }, { default: () => row.is_builtin ? "内置" : "自定义" }),
        row.is_default
          ? h(NTag, {
              size: "small",
              round: true,
              bordered: false,
              type: "success",
            }, { default: () => "当前默认" })
          : null,
      ]),
    ]),
  },
  {
    title: "正则表达式",
    key: "regex_pattern",
    minWidth: 260,
    render: (row) => h("code", { class: "rule-table__code" }, row.regex_pattern),
  },
  {
    title: "Flags / 说明",
    key: "flags",
    minWidth: 220,
    render: (row) => h("div", { class: "rule-table__secondary" }, [
      h("div", { class: "rule-table__flags" }, row.flags || "无 flags"),
      h("p", { class: "rule-table__description" }, row.description || "暂无说明"),
    ]),
  },
  {
    title: "更新时间",
    key: "updated_at",
    width: 160,
    render: (row) => h("span", { class: "rule-table__time" }, formatDate(row.updated_at)),
  },
  {
    title: "操作",
    key: "actions",
    width: 420,
    render: (row) => h(NSpace, { size: 8, wrap: true }, {
      default: () => [
        h(NButton, {
          size: "small",
          secondary: true,
          onClick: () => loadRuleIntoTest(row),
        }, { default: () => "带入测试" }),
        h(NButton, {
          size: "small",
          tertiary: true,
          onClick: () => loadRuleIntoApply(row),
        }, { default: () => "应用到书" }),
        h(NButton, {
          size: "small",
          secondary: !row.is_default,
          type: row.is_default ? "success" : "primary",
          disabled: row.is_default,
          onClick: () => { void handleSetDefault(row); },
        }, { default: () => row.is_default ? "默认中" : "设为默认" }),
        row.is_builtin
          ? null
          : h(NButton, {
              size: "small",
              tertiary: true,
              onClick: () => openEditModal(row),
            }, { default: () => "编辑" }),
        row.is_builtin
          ? null
          : h(NPopconfirm, {
              onPositiveClick: () => { void handleDelete(row); },
            }, {
              trigger: () => h(NButton, {
                size: "small",
                tertiary: true,
                type: "error",
              }, { default: () => "删除" }),
              default: () => "删除后无法恢复，确认继续吗？",
            }),
      ],
    }),
  },
]);

onMounted(() => {
  if (typeof window !== "undefined") {
    viewportWidth.value = window.innerWidth;
    window.addEventListener("resize", handleWindowResize, { passive: true });
  }

  void loadInitialData();
});

onUnmounted(() => {
  if (typeof window !== "undefined") {
    window.removeEventListener("resize", handleWindowResize);
  }
});
</script>

<style scoped>
.rule-page {
  width: min(100%, 1720px);
  margin: 0 auto;
  display: grid;
  gap: var(--space-5);
}

.rule-page__intro-stack {
  display: grid;
  gap: var(--space-3);
}

.rule-page,
.rule-page__intro-stack,
.rule-page__hero,
.rule-page__hero-copy,
.rule-page__hero-aside,
.rule-page__toolbar,
.rule-page__table-wrap,
.rule-test,
.rule-apply,
.rule-test__form,
.rule-test__result,
.rule-apply__form,
.rule-apply__result,
.rule-mobile-list,
.rule-mobile-card,
.rule-mobile-result-list,
.rule-mobile-result-card {
  min-width: 0;
}

.rule-page__hero {
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(220px, 0.75fr);
  gap: 24px;
  align-items: start;
  padding: clamp(20px, 3vw, 28px);
  border: 1px solid var(--border-color-soft);
  border-radius: var(--radius-xl);
  background:
    radial-gradient(circle at top right, rgba(52, 107, 97, 0.12), transparent 28%),
    radial-gradient(circle at bottom left, rgba(184, 93, 54, 0.1), transparent 30%),
    var(--surface-raised);
  box-shadow: var(--shadow-soft);
}

.rule-page__hero-copy {
  min-width: 0;
}

.rule-page__hero-aside {
  display: flex;
  justify-content: flex-end;
}

.rule-page__eyebrow {
  display: inline-flex;
  margin-bottom: 12px;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(52, 107, 97, 0.12);
  color: var(--accent-color);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.rule-page__title {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(28px, 3.6vw, 38px);
  line-height: 1.12;
  overflow-wrap: anywhere;
}

.rule-page__description {
  max-width: 54ch;
  margin: 12px 0 0;
  color: var(--text-secondary);
  line-height: 1.75;
  overflow-wrap: anywhere;
}

.rule-page__stats {
  display: grid;
  gap: 10px;
  min-width: 220px;
}

.rule-page__stat {
  padding: 14px 16px;
  border: 1px solid var(--border-color-soft);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.64);
}

.rule-page__stat span {
  display: block;
  color: var(--text-secondary);
  font-size: var(--text-caption);
}

.rule-page__stat strong {
  display: block;
  margin-top: 4px;
  font-size: 22px;
  line-height: 1.1;
}

.rule-page__toolbar {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  padding: 14px 18px;
  border: 1px solid var(--border-color-soft);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.68);
  box-shadow: var(--shadow-soft);
}

.rule-page__toolbar-note {
  display: grid;
  gap: 4px;
}

.rule-page__toolbar-note span {
  color: var(--text-secondary);
  font-size: var(--text-caption);
}

.rule-page__toolbar-note strong {
  font-size: 16px;
  line-height: 1.45;
}

.rule-page__toolbar-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.rule-page__toolbar-actions :deep(.n-button) {
  border-radius: var(--radius-md);
}

.rule-page__alert,
.rule-test__alert {
  border-radius: 18px;
}

.rule-page__table-card,
.rule-page__apply-card,
.rule-page__test-card {
  border: 1px solid var(--border-color-soft);
  border-radius: var(--radius-xl);
  background: var(--surface-raised);
  box-shadow: var(--shadow-soft);
}

.rule-page__table-card :deep(.n-card-header),
.rule-page__apply-card :deep(.n-card-header),
.rule-page__test-card :deep(.n-card-header) {
  align-items: center;
}

.rule-page__card-title {
  font-weight: 700;
}

.rule-page__card-subtitle {
  color: var(--text-secondary);
  font-size: 13px;
}

.rule-page__table-wrap,
.rule-test__table-wrap,
.rule-apply__table-wrap {
  overflow-x: auto;
}

.rule-mobile-list,
.rule-mobile-result-list {
  display: grid;
  gap: 12px;
}

.rule-mobile-card,
.rule-mobile-result-card {
  display: grid;
  gap: 12px;
  padding: 16px;
  border: 1px solid var(--border-color-soft);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.56);
}

.rule-mobile-card__header,
.rule-mobile-card__meta,
.rule-mobile-card__title-block,
.rule-mobile-card__section {
  display: grid;
  gap: 8px;
}

.rule-mobile-card__badges,
.rule-mobile-card__actions {
  display: grid;
  gap: 8px;
}

.rule-mobile-card__title {
  font-size: 16px;
  line-height: 1.5;
}

.rule-mobile-card__time,
.rule-mobile-card__label,
.rule-mobile-card__value,
.rule-mobile-result-card__row span,
.rule-mobile-result-card__block span {
  color: var(--text-secondary);
  font-size: 12px;
}

.rule-mobile-card__description {
  margin: 0;
  color: var(--text-primary);
  line-height: 1.75;
}

.rule-mobile-result-card__row,
.rule-mobile-result-card__block {
  display: grid;
  gap: 6px;
}

.rule-mobile-result-card__row strong {
  color: var(--text-primary);
  font-size: 14px;
}

.rule-code-block {
  display: block;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  padding: 12px 14px;
  border: 1px solid var(--border-color-soft);
  border-radius: var(--radius-md);
  background: rgba(46, 36, 29, 0.05);
  color: var(--text-primary);
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
  font-size: 12px;
  line-height: 1.7;
  white-space: pre;
  overflow-x: auto;
  overflow-y: hidden;
  box-sizing: border-box;
}

.rule-form__intro {
  margin-bottom: 16px;
  padding: 14px 16px;
  border: 1px solid var(--border-color-soft);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.58);
}

.rule-form__intro p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.7;
}

.rule-form__footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.rule-field__hint {
  display: grid;
  gap: 10px;
  width: 100%;
  margin-top: 12px;
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.7;
}

.rule-table__primary,
.rule-table__secondary {
  display: grid;
  gap: 8px;
}

.rule-table__title {
  font-size: 15px;
  line-height: 1.5;
}

.rule-table__badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.rule-table__code,
.rule-test__match-cell {
  display: block;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--text-primary);
  font-size: 12px;
  line-height: 1.7;
}

.rule-table__flags,
.rule-table__time {
  color: var(--text-secondary);
  font-size: 12px;
}

.rule-table__description {
  margin: 0;
  color: var(--text-primary);
  line-height: 1.7;
}

.rule-test,
.rule-apply {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(0, 0.9fr);
  gap: 20px;
}

.rule-test__form,
.rule-test__result,
.rule-apply__form,
.rule-apply__result {
  padding: 18px;
  border: 1px solid var(--border-color-soft);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.5);
}

.rule-test__lead,
.rule-apply__lead {
  margin-bottom: 18px;
}

.rule-test__lead strong,
.rule-apply__lead strong {
  display: block;
  font-size: 18px;
}

.rule-test__lead p,
.rule-apply__lead p {
  margin: 8px 0 0;
  color: var(--text-secondary);
  line-height: 1.8;
}

.rule-test__actions,
.rule-apply__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.rule-test__summary,
.rule-apply__summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.rule-test__summary-card,
.rule-apply__summary-card {
  padding: 14px 16px;
  border: 1px solid var(--border-color-soft);
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.78);
}

.rule-test__summary-card span,
.rule-apply__summary-card span {
  display: block;
  color: var(--text-secondary);
  font-size: 12px;
}

.rule-test__summary-card strong,
.rule-apply__summary-card strong {
  display: block;
  margin-top: 6px;
  font-size: 22px;
}

.rule-test__placeholder,
.rule-apply__placeholder {
  display: grid;
  gap: 10px;
  align-content: start;
  min-height: 100%;
  padding: 12px 4px;
}

.rule-test__placeholder strong,
.rule-apply__placeholder strong {
  font-size: 18px;
}

.rule-test__placeholder p,
.rule-apply__placeholder p,
.rule-apply__note {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.8;
}

.rule-test__empty {
  padding: 18px 0 4px;
}

.rule-page :deep(.n-base-selection),
.rule-page :deep(.n-input),
.rule-page :deep(.n-input-wrapper),
.rule-page :deep(.n-form-item),
.rule-page :deep(textarea) {
  width: 100%;
  max-width: 100%;
  min-width: 0;
  box-sizing: border-box;
}

@media (max-width: 960px) {
  .rule-page__hero,
  .rule-test,
  .rule-apply {
    grid-template-columns: 1fr;
    align-items: stretch;
  }

  .rule-page__stats {
    min-width: 0;
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .rule-page__hero-aside {
    justify-content: stretch;
  }

  .rule-page__toolbar {
    flex-direction: column;
    align-items: stretch;
  }
}

@media (max-width: 720px) {
  .rule-page__hero,
  .rule-page__toolbar {
    padding: 14px;
  }

  .rule-page {
    gap: 16px;
  }

  .rule-page__title {
    font-size: clamp(24px, 7vw, 30px);
    line-height: 1.2;
  }

  .rule-page__description {
    max-width: none;
  }

  .rule-page__stats {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 8px;
  }

  .rule-test__summary,
  .rule-apply__summary {
    grid-template-columns: 1fr;
  }

  .rule-page__hero-aside {
    justify-content: stretch;
  }

  .rule-page__stat,
  .rule-test__form,
  .rule-test__result,
  .rule-apply__form,
  .rule-apply__result,
  .rule-mobile-card,
  .rule-mobile-result-card {
    padding: 14px;
  }

  .rule-page__stat {
    padding: 12px 10px;
  }

  .rule-page__stat span {
    font-size: 11px;
    line-height: 1.4;
  }

  .rule-page__stat strong {
    font-size: 18px;
  }

  .rule-mobile-card__actions {
    grid-template-columns: 1fr;
  }

  .rule-page__toolbar-actions,
  .rule-form__footer,
  .rule-test__actions,
  .rule-apply__actions {
    display: grid;
    grid-template-columns: 1fr;
  }

  .rule-page__card-subtitle {
    display: none;
  }
}
</style>




