import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const cwd = resolve(process.cwd());
const frontendRoot = cwd.endsWith(`${process.platform === "win32" ? "\\" : "/"}frontend`)
  ? cwd
  : resolve(cwd, "frontend");
const bookshelfPath = resolve(frontendRoot, "src/pages/BookshelfPage.vue");
const readerPath = resolve(frontendRoot, "src/pages/ReaderPage.vue");

const bookshelfSource = readFileSync(bookshelfPath, "utf8");
const readerSource = readFileSync(readerPath, "utf8");

const failures = [];

function expectMatch(source, pattern, message) {
  if (!pattern.test(source)) {
    failures.push(message);
  }
}

function expectNoMatch(source, pattern, message) {
  if (pattern.test(source)) {
    failures.push(message);
  }
}

expectMatch(
  bookshelfSource,
  /\.bookshelf-page__header-actions\s*\{[\s\S]*?display:\s*flex;[\s\S]*?flex-wrap:\s*nowrap;[\s\S]*?overflow-x:\s*auto;[\s\S]*?\}/,
  "书架页工具区未保持为单行横向 flex 容器，缺少 nowrap/overflow-x 约束。",
);

expectNoMatch(
  bookshelfSource,
  /\.bookshelf-page__header-actions\s*\{[^}]*display:\s*grid;[^}]*\}/,
  "书架页工具区仍存在 grid 布局定义，会把 4 个操作项拆散。",
);

expectMatch(
  readerSource,
  /@media\s*\(max-width:\s*980px\)\s*\{[\s\S]*?\.reader-stage__stat\s*\{[^}]*display:\s*none;[^}]*\}/,
  "阅读页移动端仍未隐藏顶部进度信息块。",
);

if (failures.length > 0) {
  console.error("UI fix verification failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.log("UI fix verification passed.");
