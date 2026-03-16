<template>
  <n-modal
    :show="show"
    preset="card"
    :mask-closable="!submitting"
    :closable="!submitting"
    :style="modalStyle"
    @update:show="handleModalVisibilityChange"
  >
    <template #header>
      <span>切换后端</span>
    </template>

    <div class="backend-switcher">
      <n-alert type="info" :show-icon="false">
        当前连接：<strong>{{ currentBackendSummary }}</strong>
      </n-alert>

      <n-alert v-if="formError" type="error" :show-icon="false">
        {{ formError }}
      </n-alert>

      <n-form label-placement="top">
        <n-form-item label="连接模式">
          <n-radio-group v-model:value="draft.mode" name="backend-mode">
            <n-space vertical size="small">
              <n-radio value="local">本地后端</n-radio>
              <n-radio value="remote">远程后端</n-radio>
            </n-space>
          </n-radio-group>
          <div class="backend-switcher__hint">
            本地模式会继续使用当前 Web 的同源 `/api` 行为，或使用本地环境变量里的覆盖地址。
          </div>
        </n-form-item>

        <n-form-item label="远程后端地址">
          <n-input
            v-model:value="draft.remoteBaseUrl"
            :disabled="draft.mode !== 'remote' || submitting"
            placeholder="https://example.com"
          />
          <div class="backend-switcher__hint">
            这里只填写后端根地址，不要包含 `/api`。
          </div>
        </n-form-item>
      </n-form>
    </div>

    <template #footer>
      <div class="backend-switcher__footer">
        <n-button :disabled="submitting" @click="applyLocalDefault">
          恢复本地默认
        </n-button>
        <n-space>
          <n-button :disabled="submitting" @click="closeModal">取消</n-button>
          <n-button type="primary" :loading="submitting" @click="submit">
            保存并重新登录
          </n-button>
        </n-space>
      </div>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import {
  NAlert,
  NButton,
  NForm,
  NFormItem,
  NInput,
  NModal,
  NRadio,
  NRadioGroup,
  NSpace,
  useMessage,
} from "naive-ui";
import { useRouter } from "vue-router";

import { useAuthStore } from "../stores/auth";
import { usePreferencesStore } from "../stores/preferences";
import {
  type BackendConfig,
  type BackendMode,
  getBackendDisplaySummary,
  getBackendIdForConfig,
  getRemoteBaseUrlValidationMessage,
  isSameBackendConfig,
  loadBackendConfig,
  normalizeRemoteBaseUrl,
  saveBackendConfig,
  storeBackendNotice,
} from "../utils/backend";
import { authTokenStorage } from "../utils/token";

interface BackendDraftState {
  mode: BackendMode;
  remoteBaseUrl: string;
}

const props = defineProps<{
  show: boolean;
}>();

const emit = defineEmits<{
  (event: "update:show", value: boolean): void;
}>();

const modalStyle = {
  width: "min(560px, calc(100vw - 24px))",
};

const router = useRouter();
const message = useMessage();
const authStore = useAuthStore();
const preferencesStore = usePreferencesStore();
const submitting = ref(false);
const formError = ref<string | null>(null);
const currentConfig = ref<BackendConfig>(loadBackendConfig());
const draft = reactive<BackendDraftState>({
  mode: "local",
  remoteBaseUrl: "",
});

const currentBackendSummary = computed(() => getBackendDisplaySummary(currentConfig.value));

watch(
  () => props.show,
  (value) => {
    if (value) {
      syncDraftFromStorage();
    }
  },
);

function syncDraftFromStorage() {
  currentConfig.value = loadBackendConfig();
  draft.mode = currentConfig.value.mode;
  draft.remoteBaseUrl = currentConfig.value.remoteBaseUrl || "";
  formError.value = null;
}

function handleModalVisibilityChange(value: boolean) {
  emit("update:show", value);
}

function closeModal() {
  if (submitting.value) {
    return;
  }

  emit("update:show", false);
}

function applyLocalDefault() {
  draft.mode = "local";
  formError.value = null;
}

function buildNextConfig(): BackendConfig {
  if (draft.mode === "remote") {
    const validationMessage = getRemoteBaseUrlValidationMessage(draft.remoteBaseUrl);
    if (validationMessage) {
      throw new Error(validationMessage);
    }
  }

  return {
    mode: draft.mode,
    remoteBaseUrl: normalizeRemoteBaseUrl(draft.remoteBaseUrl),
  };
}

function clearBackendTokens(previousConfig: BackendConfig, nextConfig: BackendConfig) {
  const previousBackendId = getBackendIdForConfig(previousConfig);
  const nextBackendId = getBackendIdForConfig(nextConfig);

  authTokenStorage.clear(previousBackendId);
  authTokenStorage.clear(nextBackendId);
  authTokenStorage.clearLegacy();

  return nextBackendId;
}

async function submit() {
  formError.value = null;
  submitting.value = true;

  try {
    const nextConfig = buildNextConfig();

    if (isSameBackendConfig(currentConfig.value, nextConfig)) {
      message.info("当前已经在使用这个后端。");
      closeModal();
      return;
    }

    const savedConfig = saveBackendConfig(nextConfig);
    const nextBackendId = clearBackendTokens(currentConfig.value, savedConfig);

    authStore.handleBackendSwitch(nextBackendId);
    preferencesStore.resetState();

    storeBackendNotice({
      type: "success",
      text: `已切换到${savedConfig.mode === "remote" ? "远程" : "本地"}后端，请重新登录。`,
    });

    closeModal();
    window.location.assign(router.resolve({ name: "login" }).href);
  } catch (error) {
    const messageText = error instanceof Error ? error.message : "切换后端失败，请稍后重试。";
    formError.value = messageText;
    message.error(messageText);
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
.backend-switcher {
  display: grid;
  gap: 16px;
}

.backend-switcher__hint {
  margin-top: 10px;
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.7;
}

.backend-switcher__footer {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

@media (max-width: 640px) {
  .backend-switcher__footer {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
