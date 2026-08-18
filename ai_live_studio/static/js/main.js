// Global helpers used across the app

// Auto-init Bootstrap toasts
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.toast').forEach((el) => {
    const toast = new bootstrap.Toast(el, { delay: 4000 });
    toast.show();
  });

  const toggleBtn = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', () => sidebar.classList.toggle('open'));
    document.addEventListener('click', (e) => {
      if (window.innerWidth < 992 && sidebar.classList.contains('open')
          && !sidebar.contains(e.target) && e.target !== toggleBtn) {
        sidebar.classList.remove('open');
      }
    });
  }
});

// Read the CSRF token from the cookie (Django default cookie name)
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}

window.csrfFetch = function (url, options = {}) {
  const headers = options.headers || {};
  headers['X-CSRFToken'] = getCookie('csrftoken');
  headers['Content-Type'] = headers['Content-Type'] || 'application/json';
  return fetch(url, { ...options, headers });
};
