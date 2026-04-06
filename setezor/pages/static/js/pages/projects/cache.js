/* localStorage-кэш с TTL для данных проектов. */

const CACHE_PREFIX = "pinfo_";
const CACHE_TTL    = 3 * 60_000; // 3 минуты

function get(projectId) {
  try {
    const raw = localStorage.getItem(CACHE_PREFIX + projectId);
    if (!raw) return null;
    const { scans, cachedAt } = JSON.parse(raw);
    if (Date.now() - cachedAt > CACHE_TTL) {
      localStorage.removeItem(CACHE_PREFIX + projectId);
      return null;
    }
    return scans;
  } catch {
    return null;
  }
}

function set(projectId, scans) {
  try {
    localStorage.setItem(
      CACHE_PREFIX + projectId,
      JSON.stringify({ scans, cachedAt: Date.now() })
    );
  } catch {
    // QuotaExceededError — молча пропускаем
  }
}

function remove(projectId) {
  localStorage.removeItem(CACHE_PREFIX + projectId);
}

function evictStale(activeProjectIds) {
  const activeIds = new Set(activeProjectIds);
  for (const key of Object.keys(localStorage)) {
    if (key.startsWith(CACHE_PREFIX) && !activeIds.has(key.slice(CACHE_PREFIX.length))) {
      localStorage.removeItem(key);
    }
  }
}

export const ProjectCache = { get, set, remove, evictStale };