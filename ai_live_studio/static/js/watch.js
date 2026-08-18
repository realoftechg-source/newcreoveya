(function () {
  'use strict';

  const root = document.getElementById('watchRoot');
  if (!root) return;

  const streamId = root.dataset.streamId;
  const video = document.getElementById('watchVideo');
  const statusBadge = document.getElementById('watchStatusBadge');
  const audienceEl = document.getElementById('watchAudience');
  const connectingEl = document.getElementById('watchConnecting');
  const endedEl = document.getElementById('watchEnded');

  if (!streamId) return;

  function showEnded() {
    if (video) video.style.display = 'none';
    if (connectingEl) connectingEl.style.display = 'none';
    if (endedEl) endedEl.style.display = 'flex';
    if (statusBadge) {
      statusBadge.textContent = 'ENDED';
      statusBadge.className = 'badge-status badge-ended';
    }
  }

  async function pollStatus() {
    try {
      const res = await fetch(`/api/watch-status/${streamId}/`);
      const data = await res.json();
      if (!data.ok) {
        showEnded();
        return;
      }
      if (audienceEl) audienceEl.textContent = data.audience_count;

      if (data.status === 'live') {
        if (statusBadge) {
          statusBadge.textContent = 'LIVE';
          statusBadge.className = 'badge-status badge-live';
        }
      } else {
        showEnded();
      }
    } catch (err) { /* ignore, retry next tick */ }
  }

  pollStatus();
  setInterval(pollStatus, 5000);

  window.WebRTCViewer.connect(streamId, video, {
    onConnected: () => {
      if (connectingEl) connectingEl.style.display = 'none';
      if (video) video.style.display = 'block';
    },
    onError: () => {
      showEnded();
    },
    onEnded: () => {
      showEnded();
    },
  });
})();
