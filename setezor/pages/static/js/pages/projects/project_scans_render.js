/* Modern Project Cards UI - White Theme */

// ─── Стили (рекомендуется вынести в CSS файл) ─────────────────────────────────
const styles = `
  .project-card {
    transition: all 0.25s ease-in-out;
    border: 1.5px solid #d1d1d1 !important; /* Четкая рамка */
    border-radius: 14px;
    background: #fff;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }
  
  .project-card:hover {
    border-color: #10b981 !important; /* Рамка становится зеленой при наведении */
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.05);
    transform: translateY(-2px);
  }

  .scan-stat-box {
    background: #ffffff;
    border: 1px solid #d1d1d1;
    border-radius: 8px;
    padding: 8px;
    text-align: center;
  }
  
  .custom-carousel-indicators [data-bs-target] {
    width: 18px !important;   
    height: 4px !important;   
    border-radius: 2px;        
    border: none !important;   
    background-color: #7f8a97;
    opacity: 0.5;
    transition: all 0.3s ease;
}

.custom-carousel-indicators .active {
    width: 24px !important;   
    background-color: #1f8655 !important;
    opacity: 1 !important;
}
`;


// Добавляем стили в head, если их там нет
if (!document.getElementById('project-renderer-styles')) {
  const styleTag = document.createElement('style');
  styleTag.id = 'project-renderer-styles';
  styleTag.innerHTML = styles;
  document.head.appendChild(styleTag);
}


// ─── Утилиты ──────────────────────────────────────────────────────────────────

function spinnerHTML() {
  return `
    <div class="d-flex justify-content-center align-items-center py-5">
      <div class="spinner-border spinner-border-sm text-success" style="opacity: 0.5" role="status">
        <span class="visually-hidden">${i18next.t('Loading...')}</span>
      </div>
    </div>`;
}

// ─── Карусель сканов ──────────────────────────────────────────────────────────

function renderScansCarousel(projectId, scans) {
  const wrap = document.getElementById(`scans_carousel_wrap_${projectId}`);
  if (!wrap) return;

  if (!scans || !scans.length) {
    wrap.innerHTML = `<div class="text-center py-4 text-muted small">No active scans</div>`;
    return;
  }

  const carouselId = `scans_carousel_${projectId}`;
  const slides = scans.map((scan, i) => `
    <div class="carousel-item ${i === 0 ? "active" : ""}">
      <div class="d-flex align-items-center justify-content-center gap-2 mb-3 px-2">
        <strong class="text-truncate text-center" style="font-size: 0.85rem; color: #1e293b; max-width: 100%;">
          ${scan.scan_name}
        </strong>
      </div>
      <div class="row g-2">
        <div class="col-6">
          <div class="scan-stat-box">
            <div class="small text-muted" style="font-size: 10px;">${i18next.t('NODES')}</div>
            <div class="fw-bold">${scan.count_ip ?? 0}</div>
          </div>
        </div>
        <div class="col-6">
          <div class="scan-stat-box">
            <div class="small text-muted" style="font-size: 10px;">${i18next.t('PORTS')}</div>
            <div class="fw-bold">${scan.count_port ?? 0}</div>
          </div>
        </div>
        <div class="col-6">
          <div class="scan-stat-box">
            <div class="small text-muted" style="font-size: 10px;">${i18next.t('COMMENTS')}</div>
            <div class="fw-bold">${scan.count_comment ?? 0}</div>
          </div>
        </div>
        <div class="col-6">
          <div class="scan-stat-box">
            <div class="small text-muted" style="font-size: 10px;">${i18next.t('VULNS')}</div>
            <div class="fw-bold">${scan.count_vuln ?? 0}</div>
          </div>
        </div>
      </div>
    </div>`).join("");

  wrap.innerHTML = `
    <div id="${carouselId}" class="carousel slide" data-bs-ride="false">
      <div class="carousel-inner">${slides}</div>
      
      ${scans.length > 1 ? `
        <div class="carousel-indicators custom-carousel-indicators" 
             style="position:relative; margin-top:20px; margin-bottom:0;">
          ${scans.map((_, i) => `
            <button type="button" 
                    data-bs-target="#${carouselId}" 
                    data-bs-slide-to="${i}" 
                    class="${i === 0 ? "active" : ""}" 
                    aria-label="Slide ${i + 1}">
            </button>`).join("")}
        </div>` : ""}
    </div>`;
}


// ─── Ошибка загрузки ──────────────────────────────────────────────────────────

function renderScansError(projectId) {
  const wrap = document.getElementById(`scans_carousel_wrap_${projectId}`);
  if (!wrap) return;
  wrap.innerHTML = `
    <div class="text-center py-4" style="cursor:pointer;" data-retry-id="${projectId}">
      <p class="text-danger small mb-1 mt-2">
        <i class="bi bi-exclamation-circle me-1"></i> Failed to load
      </p>
      <span class="text-decoration-underline text-muted" style="font-size: 11px;">Tap to retry</span>
    </div>`;

  wrap.querySelector("[data-retry-id]")
    .addEventListener("click", () => window.__retryCard(projectId));
}

// ─── Спиннер ──────────────────────────────────────────────────────────────────

function renderScansSpinner(projectId) {
  const wrap = document.getElementById(`scans_carousel_wrap_${projectId}`);
  if (wrap) wrap.innerHTML = spinnerHTML();
}

// ─── Карточка проекта ─────────────────────────────────────────────────────────

function createCardHTML(project, role, ownerLogin) {
  const isOwner = role === "owner";
  
  return `
    <div id="${project.id}" class="h-100" data-project-id="${project.id}">
      <div class="card project-card h-100 shadow-none">
        
        <div class="card-header">
          <div class="d-flex justify-content-between align-items-start">
            <div class="text-truncate">
              <h6 class="fw-bold text-dark text-truncate mt-1" style="margin-bottom: 0" title="${project.name}">
                ${project.name}
              </h6>
              <span class="small text-muted" >
                ${role}${ownerLogin && !isOwner ? `: ${ownerLogin}` : ''}
              </span>
            </div>
            
            <div class="dropdown">
              <button class="btn btn-link text-muted p-0" data-bs-toggle="dropdown">
                <i class="bi bi-three-dots-vertical"></i>
              </button>
              <ul class="dropdown-menu dropdown-menu-end border shadow-sm" style="border-radius: 10px;">
                ${isOwner ? `<li><button class="dropdown-item small" data-action="export" data-project-id="${project.id}"><i class="bi bi-download me-2"></i>${i18next.t('Export')}</button></li>` : ""}
                <li><button class="dropdown-item small text-danger" data-action="delete" data-project-id="${project.id}"><i class="bi bi-trash me-2"></i>${i18next.t('Delete')}</button></li>
              </ul>
            </div>
          </div>
        </div>

        <div class="card-body d-flex flex-column px-3 pb-3 pt-3">
          <div id="scans_carousel_wrap_${project.id}" class="flex-grow-1">
            ${spinnerHTML()}
          </div>
          
          <div class="mt-3">
            <button class="btn btn-success w-100" 
                    data-action="choose"
                    data-project-id="${project.id}">
              ${i18next.t("Choose")}
            </button>
          </div>
        </div>
      </div>
    </div>`;
}


// ─── Секция ───────────────────────────────────────────────────────────────────

function renderSection(container, title, items) {
  if (!items.length) return;

  const cards = items.map(({ project, role, owner_login }) => `
    <div class="col">
      ${createCardHTML(project, role, owner_login)}
    </div>`).join("");

  const section = document.createElement("details");
  section.open = true;
  section.className = "mb-5";
  section.innerHTML = `
    <summary class="h5 fw-bold mb-4 d-flex align-items-center" style="cursor:pointer; list-style:none;">
      <i class="bi bi-chevron-right me-2 text-success transition-icon"></i>
      ${title}
    </summary>
    <div class="row row-cols-1 row-cols-sm-2 row-cols-md-3 row-cols-lg-4 row-cols-xl-5 row-cols-xxl-6 g-4">
      ${cards}
    </div>`;
  container.appendChild(section);
}

export const ProjectRenderer = {
  renderScansCarousel,
  renderScansError: (id) => {},
  renderScansSpinner,
  createCardHTML,
  renderSection,
};
