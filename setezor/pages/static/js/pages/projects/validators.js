/* Валидация пользовательского ввода. */

function projectName(name) {
  const trimmed = name.trim();
  if (!trimmed) {
    create_toast("Error", "Project name is required", "error");
    return false;
  }
  if (trimmed.length > 64) {
    create_toast("Error", "Project name is too long", "error");
    return false;
  }
  if (/[<>"'&]/.test(trimmed)) {
    create_toast("Error", "Invalid characters in project name", "error");
    return false;
  }
  return true;
}

function importFile(file) {
  if (!file) {
    create_toast("Error", "No file selected", "error");
    return false;
  }
  const ext = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
  if (ext !== ".zip") {
    create_toast("Error", "Invalid file format", "error");
    return false;
  }
  if (file.size === 0) {
    create_toast("Error", "File is empty", "error");
    return false;
  }
  return true;
}

function inviteToken(token) {
  const trimmed = token.trim();
  if (!trimmed) {
    create_toast("Error", "Token is required", "error");
    return false;
  }
  return true;
}

export const Validators = { projectName, importFile, inviteToken };