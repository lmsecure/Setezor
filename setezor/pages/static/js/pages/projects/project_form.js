/* Формы создания, импорта проекта и входа по токену. */

import { Api }        from "./api.js";
import { Validators } from "./validators.js";

async function createProject() {
  const nameInput = document.getElementById("new_project_name");
  const name = nameInput.value;

  if (!Validators.projectName(name)) {
    nameInput.classList.add("is-invalid");
    return;
  }
  nameInput.classList.remove("is-invalid");

  try {
    await Api.createProject(name.trim());
    window.location.href = "/projects_dashboard";
  } catch (err) {
    console.error("[createProject] Error:", err);
    create_toast("Error", err.message, "error");
  }
}

function importProject() {
  const fileInput = document.getElementById("projectFileInput");

  function handleFileChange(e) {
    const file = e.target.files[0];
    fileInput.removeEventListener("change", handleFileChange);

    if (!Validators.importFile(file)) {
      fileInput.value = "";
      return;
    }

    Api.importProject(file)
      .then(() => create_toast("Info", "Import project has started, please wait a few minutes", "info"))
      .catch(err => create_toast("Error", err.message, "error"));
  }

  fileInput.addEventListener("change", handleFileChange);
  fileInput.click();
}

async function enterByToken() {
  const el = document.getElementById("invite_token_enter");
  const token = el.value;

  if (!Validators.inviteToken(token)) {
    el.classList.add("is-invalid");
    return;
  }
  el.classList.remove("is-invalid");

  try {
    await Api.enterByToken(token);
    window.location.href = "/projects_dashboard";
  } catch (err) {
    console.error("[enterByToken] Error:", err);
    create_toast("Error", err.message, "error");
  }
}

function preventEnter(event) {
  if (event.key === "Enter") {
    event.preventDefault();
    document.getElementById("createProjectButton").click();
  }
}

// ─── Инициализация ────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  // Автозаполнение токена из URL (?token=...)
  const token = new URLSearchParams(window.location.search).get("token");
  if (token) {
    const tokenField = document.getElementById("invite_token_enter");
    if (tokenField) {
      tokenField.value = token;
      document.getElementById("enterByTokenButton").click();
    }
  }
});

// Экспортируем функции которые вызываются из HTML через onclick
window.createProject = createProject;
window.importProject = importProject;
window.enterByToken  = enterByToken;
window.preventEnter  = preventEnter;