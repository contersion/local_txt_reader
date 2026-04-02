import { createApp } from "vue";

import App from "./App.vue";
import { router } from "./router";
import { useAuthStore } from "./stores/auth";
import { useAppThemeStore } from "./stores/app-theme";
import { pinia } from "./stores";
import { installGlobalErrorHandling, notifyGlobalError } from "./utils/app-notifier";
import "./styles/index.css";

installGlobalErrorHandling();

const app = createApp(App);

app.config.errorHandler = (error) => {
  notifyGlobalError(error, "页面渲染出现异常，请刷新后重试");
  console.error(error);
};

router.onError((error) => {
  notifyGlobalError(error, "页面跳转失败，请稍后重试");
});

app.use(pinia);

// 应用启动时先恢复全局主题，避免页面首次渲染出现明显闪烁。
const appThemeStore = useAppThemeStore(pinia);
appThemeStore.initialize();

const authStore = useAuthStore(pinia);
void authStore.ensureReady();

app.use(router);
app.mount("#app");
