import { createRouter, createWebHistory } from "vue-router";

import AppLayout from "../layouts/AppLayout.vue";
import BookDetailPage from "../pages/BookDetailPage.vue";
import BookshelfPage from "../pages/BookshelfPage.vue";
import LoginPage from "../pages/LoginPage.vue";
import ReaderPage from "../pages/ReaderPage.vue";
import RuleManagementPage from "../pages/RuleManagementPage.vue";
import { pinia } from "../stores";
import { useAuthStore } from "../stores/auth";
import { usePreferencesStore } from "../stores/preferences";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/login",
      name: "login",
      component: LoginPage,
      meta: {
        guestOnly: true,
        title: "登录",
      },
    },
    {
      path: "/",
      component: AppLayout,
      meta: {
        requiresAuth: true,
      },
      children: [
        {
          path: "",
          redirect: {
            name: "books",
          },
        },
        {
          path: "books",
          name: "books",
          component: BookshelfPage,
          meta: {
            title: "书架",
          },
        },
        {
          path: "books/:bookId",
          name: "book-detail",
          component: BookDetailPage,
          props: (route) => ({
            bookId: Number(route.params.bookId),
          }),
          meta: {
            title: "书籍详情",
          },
        },
        {
          path: "reader/:bookId/:chapterIndex?",
          name: "reader",
          component: ReaderPage,
          props: (route) => ({
            bookId: Number(route.params.bookId),
            chapterIndex: route.params.chapterIndex ? Number(route.params.chapterIndex) : 0,
          }),
          meta: {
            title: "阅读页",
            immersive: true,
          },
        },
        {
          path: "rules",
          name: "rules",
          component: RuleManagementPage,
          meta: {
            title: "目录规则",
          },
        },
      ],
    },
    {
      path: "/:pathMatch(.*)*",
      redirect: {
        name: "books",
      },
    },
  ],
});

router.beforeEach(async (to) => {
  const authStore = useAuthStore(pinia);
  const preferencesStore = usePreferencesStore(pinia);
  await authStore.ensureReady();

  if (!authStore.isAuthenticated) {
    preferencesStore.resetState();
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return {
      name: "login",
      query: {
        redirect: to.fullPath,
      },
    };
  }

  if (to.meta.guestOnly && authStore.isAuthenticated) {
    return {
      name: "books",
    };
  }

  if (to.meta.requiresAuth && authStore.isAuthenticated) {
    await preferencesStore.ensureReady();
  }

  const pageTitle = to.meta.title ? `${String(to.meta.title)} - TXT Reader` : "TXT Reader";
  document.title = pageTitle;

  return true;
});

export { router };
