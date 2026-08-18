(function () {
  'use strict';

  const root = document.getElementById('studioRoot');
  if (!root) return;

  const streamId = root.dataset.streamId;
  const initialStatus = root.dataset.streamStatus;
  const initialLiveUrl = root.dataset.liveUrl;
  const aiEngineConnected = root.dataset.aiEngineConnected === 'true';

  const video = document.getElementById('cameraPreview');
  const placeholder = document.getElementById('cameraPlaceholder');
  const cameraWrap = document.getElementById('cameraWrap');
  const previewBtn = document.getElementById('previewBtn');
  const startBtn = document.getElementById('startBtn');
  const stopBtn = document.getElementById('stopBtn');
  const muteBtn = document.getElementById('muteBtn');
  const mirrorBtn = document.getElementById('mirrorBtn');
  const switchCameraBtn = document.getElementById('switchCameraBtn');
  const shareBtn = document.getElementById('shareBtn');
  const shareBox = document.getElementById('shareBox');
  const liveUrlInput = document.getElementById('liveUrlInput');
  const copyUrlBtn = document.getElementById('copyUrlBtn');
  const statusBadge = document.getElementById('statusBadge');
  const durationTimer = document.getElementById('durationTimer');
  const audienceCounter = document.getElementById('audienceCounter');
  const cameraSelect = document.getElementById('cameraSelect');
  const micSelect = document.getElementById('micSelect');
  const qualitySelect = document.getElementById('qualitySelect');
  const resolutionSelect = document.getElementById('resolutionSelect');
  const backgroundSelect = document.getElementById('backgroundSelect');
  const lookCards = document.querySelectorAll('.look-card');
  const aiStatusBadge = document.getElementById('aiStatusBadge');

  let localStream = null;
  let outboundStream = null;
  let isMirrored = false;
  let isMuted = false;
  let isLive = initialStatus === 'live';
  let timerInterval = null;
  let secondsElapsed = 0;
  let availableCameras = [];
  let currentCameraIndex = 0;
  let currentLookId = root.dataset.currentLookId || '';

  if (liveUrlInput && initialLiveUrl) {
    liveUrlInput.value = initialLiveUrl;
  }

  function pad(n) { return String(n).padStart(2, '0'); }

  function formatDuration(totalSeconds) {
    const h = Math.floor(totalSeconds / 3600);
    const m = Math.floor((totalSeconds % 3600) / 60);
    const s = totalSeconds % 60;
    return `${pad(h)}:${pad(m)}:${pad(s)}`;
  }

  function startTimer() {
    secondsElapsed = 0;
    durationTimer.textContent = formatDuration(0);
    timerInterval = setInterval(() => {
      secondsElapsed += 1;
      durationTimer.textContent = formatDuration(secondsElapsed);
    }, 1000);
  }

  function stopTimer() {
    clearInterval(timerInterval);
  }

  function setAiStatus(status) {
    if (!aiStatusBadge) return;
    const labels = {
      connecting: ['AI: Connecting…', 'text-info'],
      active: ['AI: Active', 'text-success'],
      fallback: ['AI: Fallback (raw camera)', 'text-warning'],
      disconnected: ['AI: Disconnected', 'text-warning'],
    };
    const [text, cls] = labels[status] || ['', 'text-muted-soft'];
    aiStatusBadge.textContent = text;
    aiStatusBadge.className = `badge bg-dark bg-opacity-75 ${cls}`;
  }

  async function listDevices() {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      availableCameras = devices.filter((d) => d.kind === 'videoinput');
      const mics = devices.filter((d) => d.kind === 'audioinput');

      if (availableCameras.length) {
        cameraSelect.innerHTML = availableCameras
          .map((d, i) => `<option value="${d.deviceId}">${d.label || 'Camera ' + (i + 1)}</option>`)
          .join('');
      }
      if (mics.length) {
        micSelect.innerHTML = mics
          .map((d, i) => `<option value="${d.deviceId}">${d.label || 'Microphone ' + (i + 1)}</option>`)
          .join('');
      }
    } catch (err) {
      console.warn('Could not enumerate devices', err);
    }
  }

  async function startCameraPreview(deviceId) {
    try {
      const constraints = {
        video: deviceId ? { deviceId: { exact: deviceId } } : true,
        audio: true,
      };
      if (localStream) {
        localStream.getTracks().forEach((t) => t.stop());
      }
      localStream = await navigator.mediaDevices.getUserMedia(constraints);
      video.srcObject = localStream;
      video.style.display = 'block';
      placeholder.style.display = 'none';
      await listDevices();
    } catch (err) {
      alert('Could not access camera/microphone. Please grant permission and try again.');
      console.error(err);
    }
  }

  previewBtn?.addEventListener('click', () => startCameraPreview());

  switchCameraBtn?.addEventListener('click', async () => {
    if (!availableCameras.length) {
      await listDevices();
    }
    if (availableCameras.length < 2) return;
    currentCameraIndex = (currentCameraIndex + 1) % availableCameras.length;
    const deviceId = availableCameras[currentCameraIndex].deviceId;
    cameraSelect.value = deviceId;
    await startCameraPreview(deviceId);
    window.csrfFetch('/api/change-camera/', {
      method: 'POST',
      body: JSON.stringify({ camera_device: deviceId }),
    });
  });

  cameraSelect?.addEventListener('change', () => {
    startCameraPreview(cameraSelect.value);
    window.csrfFetch('/api/change-camera/', {
      method: 'POST',
      body: JSON.stringify({ camera_device: cameraSelect.value }),
    });
  });

  mirrorBtn?.addEventListener('click', () => {
    isMirrored = !isMirrored;
    cameraWrap.classList.toggle('mirrored', isMirrored);
    mirrorBtn.classList.toggle('active', isMirrored);
  });

  muteBtn?.addEventListener('click', () => {
    isMuted = !isMuted;
    if (localStream) {
      localStream.getAudioTracks().forEach((t) => (t.enabled = !isMuted));
    }
    muteBtn.classList.toggle('active', isMuted);
    muteBtn.innerHTML = isMuted
      ? '<i class="bi bi-mic-mute-fill"></i>'
      : '<i class="bi bi-mic-fill"></i>';
  });

  function setActiveLookCard(lookId) {
    lookCards.forEach((card) => {
      card.classList.toggle('active', card.dataset.lookId === String(lookId));
    });
  }

  // Establishes (or re-establishes) the outbound video stream based on the
  // currently selected look, and hands it to the broadcaster. Also swaps
  // the on-screen preview over to this same stream, so you see exactly
  // what your viewers see — not just your raw camera.
  async function connectOutboundStream() {
    if (aiEngineConnected && currentLookId) {
      setAiStatus('connecting');
      const decartStream = await window.DecartRealtime.start(localStream, {
        onStatusChange: setAiStatus,
      });
      outboundStream = decartStream || localStream;
      if (!decartStream) setAiStatus('fallback');
    } else {
      outboundStream = localStream;
      if (aiStatusBadge) aiStatusBadge.textContent = '';
    }
    video.srcObject = outboundStream;
    video.play().catch(() => { /* ignore - autoplay races are harmless here */ });
    return outboundStream;
  }

  async function applyLook(lookId) {
    const res = await window.csrfFetch('/api/change-avatar/', {
      method: 'POST',
      body: JSON.stringify({ look_id: lookId || null }),
    });
    const data = await res.json();

    if (!data.ok) {
      if (data.code === 'no_credits') {
        alert(`${data.error}\n\nYou'll be taken to the credits page.`);
        window.location.href = '/billing/credits/';
      } else {
        alert(data.error || 'Could not switch look.');
      }
      return;
    }

    currentLookId = lookId || '';
    setActiveLookCard(currentLookId);

    // If we're already live, reconnect the outbound stream so the new
    // look takes effect immediately. This causes a brief (~1-2s) reconnect
    // for viewers — Decart's realtime session doesn't support swapping the
    // reference image without a new connection.
    if (isLive) {
      window.WebRTCBroadcaster.stop();
      if (window.DecartRealtime.isActive()) window.DecartRealtime.stop();
      await connectOutboundStream();
      window.WebRTCBroadcaster.start(streamId, outboundStream);
    }
  }

  lookCards.forEach((card) => {
    card.addEventListener('click', () => applyLook(card.dataset.lookId));
  });

  async function startStream() {
    if (!localStream) {
      await startCameraPreview();
    }
    try {
      const res = await window.csrfFetch('/api/start-stream/', {
        method: 'POST',
        body: JSON.stringify({
          title: 'Live Session',
          background: backgroundSelect.value,
          quality: qualitySelect.value,
          resolution: resolutionSelect.value,
        }),
      });
      const data = await res.json();
      if (!data.ok) {
        alert(data.error || 'Could not start stream.');
        return;
      }
      isLive = true;
      statusBadge.textContent = 'LIVE';
      statusBadge.className = 'badge-status badge-live';
      startBtn.disabled = true;
      stopBtn.disabled = false;
      startTimer();

      liveUrlInput.value = window.location.origin + data.live_url;
      shareBox.style.display = 'block';

      await connectOutboundStream();

      // Start accepting viewer connections (watch page + OBS Browser Source
      // both connect as "viewers" of this same broadcast).
      window.WebRTCBroadcaster.start(data.stream_id, outboundStream);
      pollAudience(data.stream_id);
    } catch (err) {
      console.error(err);
      alert('Network error starting stream.');
    }
  }

  let audiencePollTimer = null;
  function pollAudience(sId) {
    clearInterval(audiencePollTimer);
    audiencePollTimer = setInterval(async () => {
      try {
        const res = await fetch(`/api/watch-status/${sId}/`);
        const data = await res.json();
        if (data.ok && audienceCounter) {
          audienceCounter.innerHTML = `<i class="bi bi-eye-fill me-1"></i>${data.audience_count}`;
        }
      } catch (err) { /* ignore */ }
    }, 4000);
  }

  async function stopStream() {
    try {
      const res = await window.csrfFetch('/api/stop-stream/', { method: 'POST' });
      const data = await res.json();
      if (!data.ok) {
        alert(data.error || 'Could not stop stream.');
        return;
      }
      isLive = false;
      statusBadge.textContent = 'ENDED';
      statusBadge.className = 'badge-status badge-ended';
      startBtn.disabled = false;
      stopBtn.disabled = true;
      stopTimer();
      clearInterval(audiencePollTimer);
      window.WebRTCBroadcaster.stop();
      if (window.DecartRealtime.isActive()) {
        window.DecartRealtime.stop();
      }
      outboundStream = null;
      if (localStream) video.srcObject = localStream;
      if (aiStatusBadge) aiStatusBadge.textContent = '';
    } catch (err) {
      console.error(err);
      alert('Network error stopping stream.');
    }
  }

  startBtn?.addEventListener('click', startStream);
  stopBtn?.addEventListener('click', stopStream);

  shareBtn?.addEventListener('click', () => {
    shareBox.style.display = shareBox.style.display === 'none' ? 'block' : 'none';
  });

  copyUrlBtn?.addEventListener('click', () => {
    liveUrlInput.select();
    navigator.clipboard.writeText(liveUrlInput.value).then(() => {
      copyUrlBtn.innerHTML = '<i class="bi bi-check2"></i> Copied';
      setTimeout(() => { copyUrlBtn.innerHTML = '<i class="bi bi-clipboard"></i> Copy'; }, 1500);
    });
  });

  qualitySelect?.addEventListener('change', () => {
    window.csrfFetch('/api/change-quality/', {
      method: 'POST',
      body: JSON.stringify({ quality: qualitySelect.value, resolution: resolutionSelect.value }),
    });
  });

  resolutionSelect?.addEventListener('change', () => {
    window.csrfFetch('/api/change-quality/', {
      method: 'POST',
      body: JSON.stringify({ quality: qualitySelect.value, resolution: resolutionSelect.value }),
    });
  });

  backgroundSelect?.addEventListener('change', () => {
    window.csrfFetch('/api/change-background/', {
      method: 'POST',
      body: JSON.stringify({ background: backgroundSelect.value }),
    });
  });

  // If this stream was already live on page load (e.g. a refresh), resume
  // broadcasting once the camera comes back online.
  if (isLive) {
    statusBadge.textContent = 'LIVE';
    statusBadge.className = 'badge-status badge-live';
    startBtn.disabled = true;
    stopBtn.disabled = false;
    startCameraPreview().then(async () => {
      await connectOutboundStream();
      window.WebRTCBroadcaster.start(streamId, outboundStream);
      pollAudience(streamId);
    });
  }

  // Populate device labels once permission has already been granted in this session
  listDevices();
})();
