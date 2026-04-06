/* Действия над проектами: logout, выбор, экспорт, удаление, токен, clipboard. */

import { Api } from "./api.js";

// ─── Auth ─────────────────────────────────────────────────────────────────────

async function logoutFromProfile() {
  try {
    await Api.logout();
    window.location.href = "/login";
  } catch (err) {
    console.error("[logout] Error:", err);
  }
}

// ─── Выбор проекта ────────────────────────────────────────────────────────────

async function chooseProject(projectId) {
  try {
    await Api.setCurrentProject(projectId);
    window.location.href = "/projects_dashboard";
  } catch (err) {
    console.error("[chooseProject] Error:", err);
  }
}

// ─── Экспорт проекта ──────────────────────────────────────────────────────────

function exportProject(projectId) {
  const link = document.createElement("a");
  link.href = `/api/v1/project/${projectId}/export`;
  link.setAttribute("download", "");
  link.style.display = "none";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// ─── Удаление проекта ─────────────────────────────────────────────────────────

function deleteProject(projectId, projectName) {
  let container = document.getElementById("deleteProjectModalContainer");
  if (!container) {
    container = document.createElement("div");
    container.id = "deleteProjectModalContainer";
    document.body.appendChild(container);
  }

  container.innerHTML = `
    <div class="modal fade" id="deleteConfirmationModal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">${i18next.t("Project Deletion")}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            ${i18next.t("Are you sure you want to delete the project")} "${projectName}"?
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
              ${i18next.t("Cancel")}
            </button>
            <button type="button" class="btn btn-danger" id="confirmDeleteBtn">
              ${i18next.t("Delete")}
            </button>
          </div>
        </div>
      </div>
    </div>`;

  document.getElementById("confirmDeleteBtn")
    .addEventListener("click", () => confirmDeleteProject(projectId));

  new bootstrap.Modal(document.getElementById("deleteConfirmationModal")).show();
}

async function confirmDeleteProject(projectId) {
  try {
    await Api.deleteProject(projectId);
    location.reload();
  } catch (err) {
    console.error("[deleteProject] Error:", err);
  }
}

// ─── Токен регистрации ────────────────────────────────────────────────────────

async function generateRegisterToken(event) {
  event.preventDefault();
  const count = Number(document.getElementById("inviteToSetezorCount").value);

  try {
    const data = await Api.generateRegisterToken(count);
    document.getElementById("inviteToSetezorToken").value = data.token;

    const urlInput = document.getElementById("inviteToSetezorURL");
    urlInput.value = `${window.location.origin}/registration?token=${data.token}`;

    const copyBtn = document.getElementById("copyLinkBtn");
    const freshBtn = copyBtn.cloneNode(true);
    copyBtn.replaceWith(freshBtn);
    freshBtn.addEventListener("click", function () {
      urlInput.select();
      document.execCommand("copy");
      this.classList.replace("btn-outline-secondary", "btn-outline-success");
    });
  } catch (err) {
    console.error("[generateRegisterToken] Error:", err);
    alert("Error generating token: " + err.message);
  }
}

// ─── Clipboard ────────────────────────────────────────────────────────────────

function handleCopyToClipboard(event) {
  const button = event.currentTarget;
  const input  = button.closest(".input-group").querySelector("input");

  navigator.clipboard.writeText(input.value).then(() => {
    button.classList.replace("btn-outline-secondary", "btn-success");
    button.textContent = i18next.t("Copied!");
    setTimeout(() => {
      button.classList.replace("btn-success", "btn-outline-secondary");
      button.textContent = i18next.t("Copy");
    }, 2000);
  }).catch(err => console.error("[clipboard] Error:", err));
}

// ─── Инициализация ────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("logoutBtn")
    ?.addEventListener("click", logoutFromProfile);
  document.getElementById("generateRegisterTokenForm")
    ?.addEventListener("submit", generateRegisterToken);
  document.getElementById("copyBitcoinBtn")
    ?.addEventListener("click", handleCopyToClipboard);
  document.getElementById("copyDashBtn")
    ?.addEventListener("click", handleCopyToClipboard);

  // Делегирование событий для карточек проектов —
  // карточки рендерятся динамически, поэтому вешаем на контейнер
  document.getElementById("projects-container")
    ?.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-action]");
      if (!btn) return;

      const action    = btn.dataset.action;
      const projectId = btn.dataset.projectId;
      const projectName = btn.dataset.projectName;

      if (action === "choose") chooseProject(projectId);
      if (action === "delete") deleteProject(projectId, projectName);
      if (action === "export") exportProject(projectId);
    });
});