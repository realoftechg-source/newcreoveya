window.LiveChat = (function () {
  let pollTimer = null;
  let sinceId = 0;

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function renderMessage(container, msg) {
    const row = document.createElement('div');
    row.className = 'mb-1 small';
    row.innerHTML = `
      <span class="text-muted-soft" style="font-size:.7rem;">${msg.created_at}</span>
      <strong style="color:${msg.is_broadcaster ? 'var(--accent-light)' : '#eef2f1'};">${escapeHtml(msg.display_name)}${msg.is_broadcaster ? ' 🎙' : ''}:</strong>
      <span class="text-muted-soft">${escapeHtml(msg.message)}</span>
    `;
    container.appendChild(row);
    container.scrollTop = container.scrollHeight;
  }

  async function poll(streamId, container) {
    try {
      const res = await fetch(`/api/chat/${streamId}/messages/?since=${sinceId}`);
      const data = await res.json();
      if (data.ok && data.messages.length) {
        data.messages.forEach((m) => renderMessage(container, m));
        sinceId = data.next_since;
      }
    } catch (err) { /* ignore, retry next tick */ }
  }

  return {
    /**
     * start(streamId, containerEl, inputEl, sendBtnEl, options)
     * options.getDisplayName: () => string (for anonymous viewers)
     */
    start(streamId, containerEl, inputEl, sendBtnEl, options = {}) {
      sinceId = 0;
      containerEl.innerHTML = '';
      poll(streamId, containerEl);
      pollTimer = setInterval(() => poll(streamId, containerEl), 2500);

      async function send() {
        const text = inputEl.value.trim();
        if (!text) return;

        const body = { message: text };
        if (options.getDisplayName) {
          body.display_name = options.getDisplayName();
        }

        const fetchFn = window.csrfFetch || fetch;
        await fetchFn(`/api/chat/${streamId}/send/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        });
        inputEl.value = '';
        poll(streamId, containerEl);
      }

      sendBtnEl.addEventListener('click', send);
      inputEl.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') send();
      });
    },

    stop() {
      clearInterval(pollTimer);
    },
  };
})();
