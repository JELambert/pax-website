/**
 * PAX Upload Service — Client-side logic
 */

(function () {
  // State
  let currentUser = null;
  let selectedFile = null;

  // DOM refs
  const viewLogin = document.getElementById('view-login');
  const viewUpload = document.getElementById('view-upload');
  const userNav = document.getElementById('user-nav');
  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('file-input');
  const fileName = document.getElementById('file-name');
  const btnSubmit = document.getElementById('btn-submit');
  const uploadMessages = document.getElementById('upload-messages');
  const uploadSpinner = document.getElementById('upload-spinner');
  const tabUpload = document.getElementById('tab-upload');
  const tabSubmissions = document.getElementById('tab-submissions');

  // -- Init --

  async function init() {
    try {
      const resp = await fetch('/auth/me', { credentials: 'include' });
      if (resp.ok) {
        currentUser = await resp.json();
        showUploadView();
      } else {
        showLoginView();
      }
    } catch {
      showLoginView();
    }
  }

  // -- Views --

  function showLoginView() {
    viewLogin.classList.remove('hidden');
    viewUpload.classList.add('hidden');
  }

  function showUploadView() {
    viewLogin.classList.add('hidden');
    viewUpload.classList.remove('hidden');

    // Show user info in nav
    userNav.classList.remove('hidden');
    userNav.innerHTML = `
      <span class="user-info">
        ${currentUser.avatar_url ? `<img src="${currentUser.avatar_url}" alt="">` : ''}
        ${currentUser.username}
        <button class="btn-logout" onclick="logout()">Sign out</button>
      </span>
    `;
  }

  // -- Auth --

  window.logout = async function () {
    await fetch('/auth/logout', { method: 'POST', credentials: 'include' });
    currentUser = null;
    selectedFile = null;
    showLoginView();
  };

  // -- Tabs --

  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      const target = tab.dataset.tab;
      tabUpload.classList.toggle('hidden', target !== 'upload');
      tabSubmissions.classList.toggle('hidden', target !== 'submissions');

      if (target === 'submissions') {
        loadSubmissions();
      }
    });
  });

  // -- Drag and drop --

  dropZone.addEventListener('click', () => fileInput.click());

  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
  });

  dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
  });

  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
      handleFileSelect(fileInput.files[0]);
    }
  });

  function handleFileSelect(file) {
    if (!file.name.toLowerCase().endsWith('.zip')) {
      showMessage('error', 'Please select a .zip file');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      showMessage('error', 'File exceeds 10MB limit');
      return;
    }

    selectedFile = file;
    dropZone.classList.add('has-file');
    fileName.textContent = file.name + ' (' + formatBytes(file.size) + ')';
    fileName.classList.remove('hidden');
    btnSubmit.disabled = false;
    clearMessages();
  }

  // -- Upload --

  btnSubmit.addEventListener('click', async () => {
    if (!selectedFile || !currentUser) return;

    btnSubmit.disabled = true;
    uploadSpinner.classList.remove('hidden');
    clearMessages();

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const resp = await fetch('/api/upload', {
        method: 'POST',
        credentials: 'include',
        body: formData,
      });

      const data = await resp.json();

      if (resp.status === 429) {
        showMessage('error', 'Rate limit exceeded. Please try again later.');
        return;
      }

      if (data.success) {
        let html = `Pack <strong>${data.pack_name}</strong> submitted successfully! `;
        html += `<a href="${data.pr_url}" target="_blank">View PR #${data.pr_number}</a>`;
        showMessage('success', html);

        if (data.warnings && data.warnings.length > 0) {
          showMessage('warning', 'Warnings:', data.warnings);
        }

        // Reset file selection
        selectedFile = null;
        dropZone.classList.remove('has-file');
        fileName.classList.add('hidden');
        fileInput.value = '';
      } else {
        showMessage('error', 'Validation failed:', data.errors);
        if (data.warnings && data.warnings.length > 0) {
          showMessage('warning', 'Warnings:', data.warnings);
        }
        btnSubmit.disabled = false;
      }
    } catch (err) {
      showMessage('error', 'Upload failed: ' + err.message);
      btnSubmit.disabled = false;
    } finally {
      uploadSpinner.classList.add('hidden');
    }
  });

  // -- Submissions --

  async function loadSubmissions() {
    const loading = document.getElementById('submissions-loading');
    const content = document.getElementById('submissions-content');

    loading.classList.remove('hidden');
    content.classList.add('hidden');

    try {
      const resp = await fetch('/api/submissions', { credentials: 'include' });
      const submissions = await resp.json();

      if (submissions.length === 0) {
        content.innerHTML = '<div class="empty-state">No submissions yet. Upload your first pack!</div>';
      } else {
        let html = '<table class="submissions-table">';
        html += '<thead><tr><th>Pack</th><th>Status</th><th>CI</th><th>Date</th></tr></thead>';
        html += '<tbody>';

        for (const s of submissions) {
          const statusClass = s.state === 'merged' ? 'status-merged' : s.state === 'open' ? 'status-open' : 'status-closed';
          const ciClass = s.ci_status === 'success' ? 'ci-success' : s.ci_status === 'failure' ? 'ci-failure' : 'ci-pending';
          const ciLabel = s.ci_status || 'pending';
          const date = new Date(s.created_at).toLocaleDateString();

          html += `<tr>
            <td><a href="${s.url}" target="_blank">${s.title}</a></td>
            <td><span class="status-badge ${statusClass}">${s.state}</span></td>
            <td><span class="${ciClass}">${ciLabel}</span></td>
            <td>${date}</td>
          </tr>`;
        }

        html += '</tbody></table>';
        content.innerHTML = html;
      }
    } catch (err) {
      content.innerHTML = `<div class="message-box message-error">Failed to load submissions: ${err.message}</div>`;
    }

    loading.classList.add('hidden');
    content.classList.remove('hidden');
  }

  // -- Helpers --

  function showMessage(type, text, items) {
    const div = document.createElement('div');
    div.className = `message-box message-${type}`;
    div.innerHTML = text;
    if (items && items.length > 0) {
      const ul = document.createElement('ul');
      items.forEach(item => {
        const li = document.createElement('li');
        li.textContent = item;
        ul.appendChild(li);
      });
      div.appendChild(ul);
    }
    uploadMessages.appendChild(div);
  }

  function clearMessages() {
    uploadMessages.innerHTML = '';
  }

  function formatBytes(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }

  // Boot
  init();
})();
