// ─── Auth ──────────────────────────────────────────────────────────────────

async function logout() {
  const resp = await fetch("/api/v1/auth/logout_from_profile", { method: "POST" });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
}

async function generateRegisterToken(count) {
  const resp = await fetch("/api/v1/auth/generate_register_token", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ count }),
  });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

// ─── Проекты ───────────────────────────────────────────────────────────────

async function fetchProjects() {
  const resp = await fetch("/api/v1/user/projects");
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

async function fetchProjectsInfo(projectIds) {
  if (!projectIds.length) return {};
  const qs = projectIds.map(id => `projects=${encodeURIComponent(id)}`).join("&");
  const resp = await fetch(`/api/v1/user_project/info?${qs}`);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

async function setCurrentProject(projectId) {
  const resp = await fetch("/api/v1/project/set_current", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project_id: projectId }),
  });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
}

async function deleteProject(projectId) {
  const resp = await fetch(`/api/v1/project/${projectId}`, { method: "DELETE" });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
}

async function createProject(name) {
  const resp = await fetch("/api/v1/project", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  if (!resp.ok) {
    const data = await resp.json();
    throw new Error(data.detail || "Failed to create");
  }
}

async function importProject(file) {
  const formData = new FormData();
  formData.append("zip_file", file);
  const resp = await fetch("/api/v1/project/import", { method: "POST", body: formData });
  if (resp.status === 400) {
    const data = await resp.json();
    throw new Error(data.detail);
  }
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
}

async function enterByToken(token) {
  const resp = await fetch("/api/v1/project/enter_by_token", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token }),
  });
  const data = await resp.json();
  if (data !== true) throw new Error(data.detail);
}

export const Api = {
  logout,
  generateRegisterToken,
  fetchProjects,
  fetchProjectsInfo,
  setCurrentProject,
  deleteProject,
  createProject,
  importProject,
  enterByToken,
};