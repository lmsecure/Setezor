/* Батч-очередь с дебаунсом для загрузки данных проектов. */

import { Api }             from "./api.js";
import { ProjectCache }    from "./cache.js";
import { ProjectRenderer } from "./project_scans_render.js";

const BATCH_DELAY = 80;

const inFlight   = new Set();
const batchQueue = new Set();
let   batchTimer = null;

function enqueue(projectId) {
  const cached = ProjectCache.get(projectId);
  if (cached !== null) {
    ProjectRenderer.renderScansCarousel(projectId, cached);
    return;
  }
  if (inFlight.has(projectId)) return;

  batchQueue.add(projectId);
  clearTimeout(batchTimer);
  batchTimer = setTimeout(flush, BATCH_DELAY);
}

async function flush() {
  if (!batchQueue.size) return;

  const ids = [...batchQueue];
  batchQueue.clear();
  ids.forEach(id => inFlight.add(id));

  try {
    const response = await Api.fetchProjectsInfo(ids);

    for (const [projectId, scans] of Object.entries(response)) {
      const scansList = scans ?? [];
      ProjectCache.set(projectId, scansList);
      ProjectRenderer.renderScansCarousel(projectId, scansList);
      inFlight.delete(projectId);
    }

    const returnedIds = new Set(Object.keys(response));
    for (const id of ids) {
      if (!returnedIds.has(id)) {
        ProjectCache.set(id, []);
        ProjectRenderer.renderScansCarousel(id, []);
        inFlight.delete(id);
      }
    }
  } catch (e) {
    console.error("[projects/info] Batch fetch failed:", e);
    ids.forEach(id => {
      ProjectRenderer.renderScansError(id);
      inFlight.delete(id);
    });
  }
}

function retry(projectId) {
  ProjectCache.remove(projectId);
  inFlight.delete(projectId);
  ProjectRenderer.renderScansSpinner(projectId);
  enqueue(projectId);
}

export const ProjectBatch = { enqueue, retry };