// ============================================
// Kumoul SHARED — Main JavaScript
// ============================================

document.addEventListener('DOMContentLoaded', function () {
  initSidebar();
  initTheme();
  initNotifications();
  initDropdowns();
  initDragDrop();
  initUploadProgress();
  initViewToggle();
  initShareModal();
  initUserSearch();
  autoHideFlash();
  initLangToggle();
});

// ---- SIDEBAR ----
function initSidebar() {
  const sidebar = document.getElementById('sidebar');
  const mainWrapper = document.getElementById('mainWrapper');
  const toggleBtn = document.getElementById('sidebarToggle');
  const mobileBtn = document.getElementById('mobileMenuBtn');

  if (!sidebar) return;

  // Restore collapsed state
  const collapsed = localStorage.getItem('sidebar-collapsed') === 'true';
  if (collapsed && window.innerWidth > 768) {
    sidebar.classList.add('collapsed');
    mainWrapper.classList.add('sidebar-collapsed');
  }

  toggleBtn?.addEventListener('click', () => {
    if (window.innerWidth <= 768) return;
    sidebar.classList.toggle('collapsed');
    mainWrapper.classList.toggle('sidebar-collapsed');
    localStorage.setItem('sidebar-collapsed', sidebar.classList.contains('collapsed'));
  });

  // Mobile
  const overlay = document.createElement('div');
  overlay.className = 'sidebar-overlay';
  document.body.appendChild(overlay);

  mobileBtn?.addEventListener('click', () => {
    sidebar.classList.add('mobile-open');
    overlay.classList.add('show');
  });

  overlay.addEventListener('click', () => {
    sidebar.classList.remove('mobile-open');
    overlay.classList.remove('show');
  });
}

// ---- THEME ----
function initTheme() {
  const toggleBtn = document.getElementById('themeToggle');
  if (!toggleBtn) return;

  toggleBtn.addEventListener('click', async () => {
    const html = document.documentElement;
    const isDark = html.getAttribute('data-theme') === 'dark';
    const newTheme = isDark ? 'light' : 'dark';
    html.setAttribute('data-theme', newTheme);

    const icon = toggleBtn.querySelector('i');
    if (icon) {
      icon.className = newTheme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
    }

    try {
      await fetch('/api/toggle-theme', {
        method: 'POST',
        headers: { 'X-CSRFToken': getCsrf() }
      });
    } catch (e) {}
  });
}

// ---- LANGUAGE TOGGLE ----
function initLangToggle() {
  const btn = document.getElementById('langToggle');
  if (!btn) return;
  btn.addEventListener('click', () => {
    const html = document.documentElement;
    const isAr = html.getAttribute('lang') === 'ar';
    html.setAttribute('lang', isAr ? 'en' : 'ar');
    html.setAttribute('dir', isAr ? 'ltr' : 'rtl');
    btn.querySelector('span').textContent = isAr ? 'ع' : 'EN';
    // Save via profile update (simplified — just toggles UI)
  });
}

// ---- NOTIFICATIONS ----
function initNotifications() {
  const btn = document.getElementById('notifBtn');
  const dropdown = document.getElementById('notifDropdown');
  if (!btn || !dropdown) return;

  btn.addEventListener('click', (e) => {
    e.stopPropagation();
    const isOpen = dropdown.classList.contains('open');
    closeAllDropdowns();
    if (!isOpen) {
      dropdown.classList.add('open');
      loadNotifications();
    }
  });

  document.addEventListener('click', () => dropdown.classList.remove('open'));
}

async function loadNotifications() {
  const list = document.getElementById('notifList');
  if (!list) return;
  try {
    const res = await fetch('/api/notifications/unread');
    const data = await res.json();

    const dot = document.getElementById('notifDot');
    if (dot) dot.style.display = data.count > 0 ? 'block' : 'none';

    if (!data.notifications.length) {
      list.innerHTML = '<div class="notif-loading" style="padding:20px;text-align:center;color:var(--text-3)"><i class="bi bi-bell-slash"></i><br>No new notifications</div>';
      return;
    }

    list.innerHTML = data.notifications.map(n => `
      <a href="${n.link}" class="notif-item ${n.is_read ? '' : 'unread'}">
        <div class="notif-icon ${n.type}">
          <i class="bi bi-${n.type === 'share' ? 'share' : n.type === 'announcement' ? 'megaphone' : 'info-circle'}-fill"></i>
        </div>
        <div class="notif-content">
          <div class="notif-title">${n.title}</div>
          <div class="notif-msg">${n.message || ''}</div>
          <div class="notif-time">${n.created_at}</div>
        </div>
      </a>
    `).join('');
  } catch (e) {
    console.error('Failed to load notifications', e);
  }
}

async function markAllRead() {
  try {
    await fetch('/notifications/mark-read', {
      method: 'POST',
      headers: { 'X-CSRFToken': getCsrf() }
    });
    const dot = document.getElementById('notifDot');
    if (dot) dot.style.display = 'none';
    loadNotifications();
  } catch (e) {}
}

// ---- DROPDOWNS ----
function initDropdowns() {
  const userBtn = document.getElementById('userMenuBtn');
  const userDrop = document.getElementById('userDropdown');
  if (!userBtn || !userDrop) return;

  userBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    const isOpen = userDrop.classList.contains('open');
    closeAllDropdowns();
    if (!isOpen) userDrop.classList.add('open');
  });

  document.addEventListener('click', closeAllDropdowns);
}

function closeAllDropdowns() {
  document.querySelectorAll('.user-dropdown, .notif-dropdown').forEach(d => d.classList.remove('open'));
}

// ---- DRAG AND DROP UPLOAD ----
function initDragDrop() {
  const zone = document.getElementById('uploadZone');
  if (!zone) return;

  const input = zone.querySelector('input[type="file"]');

  zone.addEventListener('click', () => input?.click());

  zone.addEventListener('dragover', (e) => {
    e.preventDefault();
    zone.classList.add('drag-over');
  });

  zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));

  zone.addEventListener('drop', (e) => {
    e.preventDefault();
    zone.classList.remove('drag-over');
    if (input && e.dataTransfer.files.length) {
      input.files = e.dataTransfer.files;
      updateFileList(input.files);
    }
  });

  input?.addEventListener('change', () => updateFileList(input.files));
}

function updateFileList(files) {
  const container = document.getElementById('filePreviewList');
  if (!container) return;
  container.innerHTML = '';
  Array.from(files).forEach(f => {
    const size = formatBytes(f.size);
    const div = document.createElement('div');
    div.className = 'file-preview-item';
    div.style.cssText = 'display:flex;align-items:center;gap:10px;padding:8px 12px;background:var(--bg);border-radius:8px;margin-top:8px;font-size:13px;';
    div.innerHTML = `
      <i class="bi bi-file-earmark" style="font-size:18px;color:var(--navy)"></i>
      <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${f.name}</span>
      <span style="color:var(--text-3);font-size:11px">${size}</span>
    `;
    container.appendChild(div);
  });
}

// ---- UPLOAD PROGRESS ----
function initUploadProgress() {
  const form = document.getElementById('uploadForm');
  if (!form) return;

  form.addEventListener('submit', function (e) {
    const fileInput = form.querySelector('input[type="file"]');
    if (!fileInput || !fileInput.files.length) {
      e.preventDefault();
      showToast('Please select at least one file.', 'warning');
      return;
    }

    const progressBar = document.getElementById('uploadProgressBar');
    const progressWrap = document.getElementById('uploadProgressWrap');
    const submitBtn = form.querySelector('button[type="submit"]');

    if (progressWrap) progressWrap.style.display = 'block';
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Uploading...';
    }

    // Fake progress animation (actual upload happens natively)
    if (progressBar) {
      let progress = 0;
      const interval = setInterval(() => {
        progress = Math.min(progress + Math.random() * 15, 90);
        progressBar.style.width = progress + '%';
        if (progress >= 90) clearInterval(interval);
      }, 200);
    }
  });
}

// ---- VIEW TOGGLE (grid/list) ----
function initViewToggle() {
  const gridBtn = document.getElementById('viewGrid');
  const listBtn = document.getElementById('viewList');
  const gridView = document.getElementById('filesGrid');
  const listView = document.getElementById('filesList');

  if (!gridBtn || !listBtn) return;

  const savedView = localStorage.getItem('files-view') || 'grid';
  setView(savedView);

  gridBtn.addEventListener('click', () => setView('grid'));
  listBtn.addEventListener('click', () => setView('list'));

  function setView(v) {
    if (v === 'grid') {
      if (gridView) gridView.style.display = 'grid';
      if (listView) listView.style.display = 'none';
      gridBtn.classList.add('active');
      listBtn.classList.remove('active');
    } else {
      if (gridView) gridView.style.display = 'none';
      if (listView) listView.style.display = 'block';
      listBtn.classList.add('active');
      gridBtn.classList.remove('active');
    }
    localStorage.setItem('files-view', v);
  }
}

// ---- SHARE MODAL ----
function initShareModal() {
  const btns = document.querySelectorAll('[data-share-file]');
  btns.forEach(btn => {
    btn.addEventListener('click', () => {
      const fileId = btn.getAttribute('data-share-file');
      const fileName = btn.getAttribute('data-file-name') || 'File';
      openShareModal(fileId, fileName);
    });
  });
}

function openShareModal(fileId, fileName) {
  const modal = document.getElementById('shareModal');
  if (!modal) return;
  document.getElementById('shareFileName').textContent = fileName;
  document.getElementById('shareFileId').value = fileId;
  document.getElementById('shareForm').action = `/share/${fileId}`;
  modal.classList.add('open');
}

function closeModal(id) {
  const modal = document.getElementById(id || 'shareModal');
  if (modal) modal.classList.remove('open');
}

// ---- USER SEARCH (for share) ----
function initUserSearch() {
  const input = document.getElementById('recipientInput');
  if (!input) return;

  const suggestions = document.getElementById('userSuggestions');
  let debounceTimer;

  input.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    const q = input.value.trim();
    if (q.length < 2) {
      suggestions?.classList.remove('show');
      return;
    }
    debounceTimer = setTimeout(() => fetchUserSuggestions(q), 200);
  });

  document.addEventListener('click', (e) => {
    if (!input.contains(e.target)) suggestions?.classList.remove('show');
  });
}

async function fetchUserSuggestions(q) {
  const suggestions = document.getElementById('userSuggestions');
  if (!suggestions) return;

  try {
    const res = await fetch(`/api/users/search?q=${encodeURIComponent(q)}`);
    const users = await res.json();
    if (!users.length) { suggestions.classList.remove('show'); return; }

    suggestions.innerHTML = users.map(u => `
      <div class="suggestion-item" onclick="selectUser('${u.username}', '${u.full_name}')">
        <div class="suggestion-avatar">${u.initials}</div>
        <div>
          <div style="font-weight:600;font-size:13px">${u.full_name}</div>
          <div style="font-size:11px;color:var(--text-3)">@${u.username} · ${u.department}</div>
        </div>
      </div>
    `).join('');

    suggestions.classList.add('show');
  } catch (e) {}
}

function selectUser(username, fullName) {
  const input = document.getElementById('recipientInput');
  if (input) input.value = username;
  const suggestions = document.getElementById('userSuggestions');
  if (suggestions) suggestions.classList.remove('show');
}

// ---- AUTO-HIDE FLASH ----
function autoHideFlash() {
  document.querySelectorAll('.flash-msg').forEach(el => {
    setTimeout(() => {
      el.style.opacity = '0';
      el.style.transition = 'opacity 0.4s';
      setTimeout(() => el.remove(), 400);
    }, 5000);
  });
}

// ---- TOAST ----
function showToast(msg, type = 'info') {
  const container = document.querySelector('.flash-container') || (() => {
    const c = document.createElement('div');
    c.className = 'flash-container';
    document.querySelector('.page-content')?.prepend(c);
    return c;
  })();

  const div = document.createElement('div');
  div.className = `flash-msg flash-${type}`;
  div.innerHTML = `<i class="bi bi-info-circle-fill"></i> ${msg} <button onclick="this.parentElement.remove()">×</button>`;
  container.appendChild(div);
  setTimeout(() => div.remove(), 5000);
}

// ---- HELPERS ----
function getCsrf() {
  return document.querySelector('meta[name="csrf-token"]')?.content ||
         document.querySelector('[name="csrf_token"]')?.value || '';
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

// Confirm before delete
document.addEventListener('click', function (e) {
  const btn = e.target.closest('[data-confirm]');
  if (!btn) return;
  const msg = btn.getAttribute('data-confirm') || 'Are you sure?';
  if (!confirm(msg)) e.preventDefault();
});

// Format bytes global for Jinja (not needed but kept for consistency)
window.formatBytes = formatBytes;
window.markAllRead = markAllRead;
window.closeModal = closeModal;
window.openShareModal = openShareModal;
window.selectUser = selectUser;
