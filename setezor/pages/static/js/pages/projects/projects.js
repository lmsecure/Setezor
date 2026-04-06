/* Точка входа. Загрузка проектов и запуск lazy loading. */

import { Api }             from "./api.js";
import { ProjectCache }    from "./cache.js";
import { ProjectRenderer } from "./project_scans_render.js";
import { ProjectBatch }    from "./batch.js";

// Retry доступен из renderScansError через window
window.__retryCard = (projectId) => ProjectBatch.retry(projectId);

// ─── Lazy loading ─────────────────────────────────────────────────────────────

function initLazyCards() {
  const cards = document.querySelectorAll("[data-project-id]");
  if (!cards.length) {
    console.warn("[projects] no cards found");
    return;
  }

  const observer = new IntersectionObserver(
    (entries, obs) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        obs.unobserve(entry.target);
        ProjectBatch.enqueue(entry.target.dataset.projectId);
      }
    },
    { rootMargin: "0px 0px 200px 0px", threshold: 0 }
  );

  cards.forEach(card => observer.observe(card));
}

// ─── Загрузка проектов ────────────────────────────────────────────────────────

async function loadProjects() {
  const container = document.getElementById("projects-container");
  if (!container) return;

  try {
    const projects = await Api.fetchProjects();

    const owned  = projects.filter(p => p.role === "owner");
    const shared = projects.filter(p => p.role !== "owner");

    const normalize = p => ({
      project: { id: p.project_id, name: p.project_name ?? p.project_id },
      role: p.role,
      owner_login: p.owner_login,
    });

    ProjectRenderer.renderSection(container, i18next.t("My projects"),     owned.map(normalize));
    ProjectRenderer.renderSection(container, i18next.t("Shared projects"), shared.map(normalize));

    ProjectCache.evictStale(projects.map(p => p.project_id));

    initLazyCards();
  } catch (e) {
    console.error("[projects] Failed to load:", e);
    container.innerHTML = `<p class="text-danger">Failed to load projects</p>`;
  }
}

// ─── Точка входа ──────────────────────────────────────────────────────────────

function init() {
  if (window.i18nReady) {
    loadProjects();
  } else {
    document.addEventListener("i18nReady", loadProjects, { once: true });
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}

window.__reloadProjects = async () => {
  const container = document.getElementById("projects-container");
  if (container) container.innerHTML = "";
  await loadProjects();
};