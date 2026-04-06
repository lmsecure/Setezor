/**
 * lazy_analytics.js
 *
 * Три уровня приоритета загрузки для каждой карточки проекта.
 * Эндпоинты: /api/v1/analytics/card/*  (project_id берётся из куки/сессии
 * через get_current_project — передаём его как query-параметр ?project_id=)
 *
 *  P1 — /card/counts       ip_count + port_count  ─┐ параллельно,
 *  P2 — /card/top_ports    первый слайд            ─┘ при входе в viewport
 *  P3 — /card/top_protocols, /card/device_types,
 *        /card/top_products  ── только при листании карусели к нужному слайду
 */

(function () {
  "use strict";

  // ─── Конфиг слайдов ────────────────────────────────────────────────────────
  const SLIDE_CONFIG = [
    { index: 0, key: "top_ports",     endpoint: "top_ports",     priority: 2 },
    { index: 1, key: "top_protocols", endpoint: "top_protocols", priority: 3 },
    { index: 2, key: "device_types",  endpoint: "device_types",  priority: 3 },
    { index: 3, key: "top_products",  endpoint: "top_products",  priority: 3 },
  ];

  // ─── Дедупликация запросов ─────────────────────────────────────────────────
  const loaded = {};
  const markLoaded = (pid, ep) => ((loaded[pid] ??= {})[ep] = true);
  const isLoaded   = (pid, ep) => !!loaded[pid]?.[ep];

  // ─── Plotly ────────────────────────────────────────────────────────────────
  const chartPx = () =>
    12 * parseFloat(getComputedStyle(document.documentElement).fontSize);

  function renderDonut(elementId, values, labels) {
    const empty = !values?.length;
    Plotly.newPlot(
      elementId,
      [{
        values: empty ? [1] : values,
        labels: empty ? ["No Data"] : labels,
        type: "pie",
        textinfo: "label",
        textposition: "inside",
        hole: 0.4,
        ...(empty && { marker: { colors: ["#ddd"] } }),
      }],
      {
        margin: { t: 5, b: 5, l: 5, r: 5 },
        showlegend: false,
        annotations: [{ text: "", showarrow: false }],
        height: chartPx(),
        width: chartPx(),
      },
      { displayModeBar: false }
    );
  }

  function showDonut(projectId, key, values, labels) {
    const skeleton = document.getElementById(`skeleton_${key}_${projectId}`);
    const donut    = document.getElementById(`${key}_${projectId}_donut`);
    if (!donut) return;
    renderDonut(donut.id, values ?? [], labels ?? []);
    skeleton?.style.setProperty("display", "none");
    donut.style.removeProperty("display");
  }

  // ─── Fetch-хелпер ─────────────────────────────────────────────────────────
  async function fetchCard(endpoint, projectId) {
    const resp = await fetch(`/api/v1/analytics/card/${projectId}/${endpoint}`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  }

  // ─── P1: счётчики ─────────────────────────────────────────────────────────
  async function loadCounts(projectId) {
    if (isLoaded(projectId, "counts")) return;
    markLoaded(projectId, "counts");
    try {
      const { ip_count, port_count } = await fetchCard("counts", projectId);
      const ipEl   = document.getElementById(`ip_count_${projectId}`);
      const portEl = document.getElementById(`port_count_${projectId}`);
      if (ipEl)   ipEl.textContent   = ip_count   ?? "—";
      if (portEl) portEl.textContent = port_count ?? "—";
    } catch (e) {
      console.warn(`[card/counts] project ${projectId}:`, e);
    }
  }

  // ─── P2 / P3: слайд ───────────────────────────────────────────────────────
  async function loadSlide(projectId, key, endpoint) {
    if (isLoaded(projectId, endpoint)) return;
    markLoaded(projectId, endpoint);
    try {
      const { data, labels } = await fetchCard(endpoint, projectId);
      showDonut(projectId, key, data, labels);
    } catch (e) {
      console.warn(`[card/${endpoint}] project ${projectId}:`, e);
      showDonut(projectId, key, [], []);
    }
  }

  // ─── При входе в viewport: P1 + P2 параллельно ────────────────────────────
  function loadVisible(projectId) {
    loadCounts(projectId);
    loadSlide(projectId, "top_ports", "top_ports");
  }

  // ─── Carousel → P3 по требованию ──────────────────────────────────────────
  function attachCarouselListener(cardEl) {
    const projectId  = cardEl.dataset.projectId;
    const carouselEl = cardEl.querySelector(".carousel");
    if (!carouselEl) return;

    carouselEl.addEventListener("slide.bs.carousel", (e) => {
      const cfg = SLIDE_CONFIG.find((s) => s.index === e.to && s.priority === 3);
      if (cfg) loadSlide(projectId, cfg.key, cfg.endpoint);
    });
  }

  // ─── IntersectionObserver ─────────────────────────────────────────────────
  function initLazyCards() {
    const cards = document.querySelectorAll("[data-project-id]");
    if (!cards.length) return;

    const observer = new IntersectionObserver(
      (entries, obs) => {
        for (const entry of entries) {
          if (!entry.isIntersecting) continue;
          obs.unobserve(entry.target);
          loadVisible(entry.target.dataset.projectId);
        }
      },
      { rootMargin: "0px 0px 200px 0px", threshold: 0 }
    );

    cards.forEach((card) => {
      observer.observe(card);
      attachCarouselListener(card);
    });
  }

  // ─── Точка входа ──────────────────────────────────────────────────────────
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initLazyCards);
  } else {
    initLazyCards();
  }
})();