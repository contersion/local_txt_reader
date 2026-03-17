import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const cwd = resolve(process.cwd());
const frontendRoot = cwd.endsWith(`${process.platform === "win32" ? "\\" : "/"}frontend`)
  ? cwd
  : resolve(cwd, "frontend");

const notifierPath = resolve(frontendRoot, "src/utils/app-notifier.ts");
const mainPath = resolve(frontendRoot, "src/main.ts");

const notifierSource = readFileSync(notifierPath, "utf8");
const mainSource = readFileSync(mainPath, "utf8");
const failures = [];

function expectMatch(source, pattern, message) {
  if (!pattern.test(source)) {
    failures.push(message);
  }
}

expectMatch(
  mainSource,
  /installGlobalErrorHandling\(\);/,
  "main.ts 仍需在应用启动时安装全局错误处理。",
);

expectMatch(
  mainSource,
  /app\.config\.errorHandler\s*=\s*\(error\)\s*=>\s*\{[\s\S]*notifyGlobalError\(error,\s*"页面渲染出现异常，请刷新后重试"\)/,
  "main.ts 仍需保留 Vue 渲染异常到 notifyGlobalError 的链路。",
);

expectMatch(
  mainSource,
  /router\.onError\(\(error\)\s*=>\s*\{[\s\S]*notifyGlobalError\(error,\s*"页面跳转失败，请稍后重试"\)/,
  "main.ts 仍需保留路由异常到 notifyGlobalError 的链路。",
);

expectMatch(
  notifierSource,
  /ResizeObserver loop completed with undelivered notifications\./,
  "app-notifier.ts 还没有声明已知的 ResizeObserver 浏览器告警文案。",
);

expectMatch(
  notifierSource,
  /ResizeObserver loop limit exceeded/,
  "app-notifier.ts 还没有覆盖 ResizeObserver 的另一条常见浏览器告警文案。",
);

expectMatch(
  notifierSource,
  /function isIgnoredWindowErrorEvent\(event: ErrorEvent\)/,
  "app-notifier.ts 还没有为 window error 事件提供精确过滤函数。",
);

expectMatch(
  notifierSource,
  /event\.error\s*!=\s*null|event\.error\s*!==\s*undefined|event\.error\s*instanceof Error/,
  "过滤逻辑需要显式区分带 error 对象的真正运行时异常。",
);

expectMatch(
  notifierSource,
  /event\.filename[\s\S]*event\.lineno[\s\S]*event\.colno/,
  "过滤逻辑需要检查来源位置信息，避免误吞真实脚本异常。",
);

expectMatch(
  notifierSource,
  /window\.addEventListener\("error",\s*\(event\)\s*=>\s*\{[\s\S]*if\s*\(isIgnoredWindowErrorEvent\(event\)\)\s*\{\s*return;\s*\}[\s\S]*notifyGlobalError\(event\.error\s*\?\?\s*event\.message,\s*"页面出现异常，请刷新后重试"\);[\s\S]*\}\);/,
  "window error 监听器还没有在 notifyGlobalError 前精确过滤 ResizeObserver 噪声。",
);

expectMatch(
  notifierSource,
  /window\.addEventListener\("unhandledrejection",\s*\(event\)\s*=>\s*\{[\s\S]*notifyGlobalError\(event\.reason,\s*"请求处理失败，请稍后重试"\);[\s\S]*\}\);/,
  "unhandledrejection 链路应保持不变，不能顺手吞掉真正 Promise 异常。",
);

if (failures.length > 0) {
  console.error("Global error filter verification failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.log("Global error filter verification passed.");
