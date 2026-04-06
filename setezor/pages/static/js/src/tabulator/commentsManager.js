/**
 * CRUD-модалка комментариев к IP.
 *
 * Использование:
 *   import CommentsManager from './commentsManager.js';
 *   const mgr = new CommentsManager();
 *   mgr.open('ip-uuid', 'ip_info');
 *
 *   window.__commentsManager = mgr; // доступ из форматтера
 */

export default class CommentsManager {
  open(ip_id, tabName) {
    this._load(ip_id, tabName);
  }

  // ─── Private ───────────────────────────────────────────────────────────────

  async _load(ip_id, tabName) {
    try {
      const { data: comments } = await axios.get(`/api/v1/vis/comment/${ip_id}`);
      const container = document.getElementById(`${tabName}commentsContainer`);
      if (!container) return;
      container.innerHTML = this._buildHTML(comments, ip_id, tabName);

      const modalEl = document.getElementById(`${tabName}commentsModal`);
      (bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl)).show();
    } catch(e) {
      console.error('Error loading comments:', e);
    }
  }

  _buildHTML(comments, ip_id, tabName) {
    const t = key => (typeof i18next !== 'undefined' ? i18next.t(key) : key);

    let html = `
      <div class="mb-3">
        <form onsubmit="window.__commentsManager._addComment(event,'${ip_id}','${tabName}')">
          <div class="form-group mb-2">
            <textarea class="form-control" id="newCommentText-${tabName}" rows="3"
              placeholder="${t('Write a comment...')}" required></textarea>
          </div>
          <div class="d-flex justify-content-end">
            <button type="submit" class="btn btn-success btn-sm">${t('Add Comment')}</button>
          </div>
        </form>
      </div><hr>`;

    (comments || []).filter(c => !c.deleted_at).forEach(comment => {
      html += this._buildComment(comment, ip_id, tabName, false);
      (comment.child_comments || []).filter(c => !c.deleted_at).forEach(child => {
        html += this._buildComment(child, ip_id, tabName, true);
      });
    });

    return html;
  }

  _buildComment(comment, ip_id, tabName, isChild) {
    const t      = key => (typeof i18next !== 'undefined' ? i18next.t(key) : key);
    const date   = new Date(comment.updated_at || comment.created_at);
    const dateStr = `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
    const indent = isChild ? 'ms-4' : '';
    const bg     = isChild ? 'style="background:#f8f9fa;"' : '';
    const tag    = isChild ? 'p' : 'h6';

    const replyBtn = !isChild
      ? `<button class="btn btn-outline-secondary btn-sm"
           onclick="window.__commentsManager._replyTo('${comment.id}','${ip_id}','${tabName}')">
           ${t('Reply')}</button>`
      : '';

    return `
      <div id="commentContainer-${comment.id}" class="comment mb-3 p-3 border rounded ${indent}" ${bg}>
        <div class="comment-content mb-2">
          <${tag} class="mb-2">${this._sanitize(comment.text)}</${tag}>
        </div>
        <div class="d-flex justify-content-between align-items-center">
          <div class="comment-meta">
            <span class="text-muted small d-block">${comment.login}</span>
            <span class="text-muted small">${dateStr}</span>
          </div>
          <div class="comment-actions" style="display:flex;gap:5px;">
            <button class="btn btn-outline-danger btn-sm"
              onclick="window.__commentsManager._delete('${comment.id}','${tabName}','${ip_id}')">
              ${t('Delete')}</button>
            <button class="btn btn-outline-primary btn-sm"
              onclick="window.__commentsManager._editStart('${comment.id}')">
              ${t('Edit')}</button>
            ${replyBtn}
          </div>
        </div>
      </div>`;
  }

  async _addComment(event, ip_id, tabName) {
    event.preventDefault();
    const textarea = document.getElementById(`newCommentText-${tabName}`);
    const text     = textarea.value.trim();
    if (!text) return;
    try {
      await axios.post('/api/v1/vis/comment', { text, ip_id }, { headers: { 'Content-Type': 'application/json' } });
      textarea.value = '';
      this._load(ip_id, tabName);
      if (typeof addTableNodesWithComments === 'function') addTableNodesWithComments();
    } catch(e) {
      console.error('Error adding comment:', e);
      alert(i18next.t('Error adding comment'));
    }
  }

  _editStart(commentId) {
    const container  = document.getElementById(`commentContainer-${commentId}`);
    const textEl     = container.querySelector('.comment-content h6, .comment-content p');
    const actionsDiv = container.querySelector('.comment-actions');
    const textarea   = document.createElement('textarea');
    textarea.className = 'form-control'; textarea.value = textEl.textContent; textarea.rows = 3;
    textarea.dataset.originalContent = textEl.innerHTML;
    textarea.dataset.originalTag     = textEl.tagName.toLowerCase();
    textEl.replaceWith(textarea);

    const btns      = document.createElement('div');
    btns.className  = 'edit-buttons mt-2'; btns.style.cssText = 'display:flex;gap:5px;';
    const cancelBtn = document.createElement('button');
    cancelBtn.className   = 'btn btn-outline-secondary btn-sm';
    cancelBtn.textContent = i18next.t('Cancel');
    cancelBtn.onclick     = () => this._editCancel(commentId);
    const saveBtn = document.createElement('button');
    saveBtn.className   = 'btn btn-outline-success btn-sm';
    saveBtn.textContent = i18next.t('Save');
    saveBtn.onclick     = () => this._editSave(commentId);
    btns.append(cancelBtn, saveBtn);
    container.querySelector('.comment-content').appendChild(btns);
    actionsDiv.style.display = 'none';
  }

  _editCancel(commentId) {
    const container = document.getElementById(`commentContainer-${commentId}`);
    const textarea  = container.querySelector('textarea');
    const el        = document.createElement(textarea.dataset.originalTag);
    el.className = 'mb-2'; el.innerHTML = textarea.dataset.originalContent;
    textarea.replaceWith(el);
    container.querySelector('.edit-buttons')?.remove();
    container.querySelector('.comment-actions').style.display = 'flex';
  }

  async _editSave(commentId) {
    const container = document.getElementById(`commentContainer-${commentId}`);
    const textarea  = container.querySelector('textarea');
    const newText   = textarea.value.trim();
    const tag       = textarea.dataset.originalTag;
    if (!newText) { alert(i18next.t('Comment cannot be empty')); return; }
    try {
      await axios.put(
        `/api/v1/vis/comment/${commentId}?comment_text=${encodeURIComponent(newText)}`,
        null, { headers: { 'Content-Type': 'application/json' } }
      );
      const el = document.createElement(tag);
      el.className = 'mb-2'; el.style.cssText = 'word-break:break-word;white-space:pre-wrap;';
      el.textContent = newText;
      textarea.replaceWith(el);
      container.querySelector('.edit-buttons')?.remove();
      container.querySelector('.comment-actions').style.display = 'flex';
      if (typeof addTableNodesWithComments === 'function') addTableNodesWithComments();
    } catch(e) {
      console.error('Error updating comment:', e);
      alert(i18next.t('Error updating comment'));
      this._editCancel(commentId);
    }
  }

  async _delete(commentId, tabName, ip_id) {
    if (!confirm(i18next.t('Are you sure you want to delete this comment?'))) return;
    try {
      await axios.delete(`/api/v1/vis/comment/${commentId}`);
      this._load(ip_id, tabName);
      if (typeof addTableNodesWithComments === 'function') addTableNodesWithComments();
    } catch(e) {
      console.error('Error deleting comment:', e);
      alert(i18next.t('Error deleting comment'));
    }
  }

  _replyTo(commentId, ip_id, tabName) {
    const replyFormId = `replyForm-${commentId}`;
    const existing    = document.getElementById(replyFormId);
    if (existing) { existing.remove(); return; }

    const form = document.createElement('div');
    form.id = replyFormId; form.className = 'reply-form mt-3 p-3 border rounded bg-light';
    form.innerHTML = `
      <form onsubmit="window.__commentsManager._submitReply(event,'${commentId}','${ip_id}','${tabName}')">
        <div class="form-group mb-2">
          <textarea class="form-control" id="replyText-${commentId}" rows="2"
            placeholder="${i18next.t('Write a reply...')}" required></textarea>
        </div>
        <div class="d-flex justify-content-end gap-2">
          <button type="button" class="btn btn-outline-secondary btn-sm"
            onclick="document.getElementById('${replyFormId}').remove()">
            ${i18next.t('Cancel')}</button>
          <button type="submit" class="btn btn-success btn-sm">${i18next.t('Send Reply')}</button>
        </div>
      </form>`;
    document.getElementById(`commentContainer-${commentId}`)?.appendChild(form);
  }

  async _submitReply(event, parentCommentId, ip_id, tabName) {
    event.preventDefault();
    const text = document.getElementById(`replyText-${parentCommentId}`)?.value.trim();
    if (!text) return;
    try {
      await axios.post('/api/v1/vis/comment',
        { text, parent_comment_id: parentCommentId, ip_id },
        { headers: { 'Content-Type': 'application/json' } }
      );
      document.getElementById(`replyForm-${parentCommentId}`)?.remove();
      this._load(ip_id, tabName);
      if (typeof addTableNodesWithComments === 'function') addTableNodesWithComments();
    } catch(e) {
      console.error('Error adding reply:', e);
      alert(i18next.t('Error adding reply'));
    }
  }

  _sanitize(str) {
    const el = document.createElement('div');
    el.textContent = str;
    return el.innerHTML;
  }
}