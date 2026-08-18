/**
 * Lightweight browser-to-browser WebRTC helper using HTTP-poll signaling
 * against the Django backend (api/webrtc.py + api/views.py). No websocket
 * server or media server required — good for demos, local networks, and
 * small audiences. For large public audiences you'd swap this signaling
 * layer for a proper SFU, but the polling contract keeps that a backend
 * change only.
 */

const ICE_SERVERS = [
  { urls: 'stun:stun.l.google.com:19302' },
  { urls: 'stun:stun1.l.google.com:19302' },
];

function apiUrl(path) {
  return path;
}

/**
 * BROADCASTER — call start(streamId, localStream) once you have a
 * MediaStream to send. Polls for new viewers and negotiates a
 * PeerConnection per viewer.
 */
window.WebRTCBroadcaster = (function () {
  let streamId = null;
  let localStream = null;
  let pollTimer = null;
  const peers = {}; // viewer_id -> { pc, iceSince }
  let onViewerCountChange = null;

  async function pollPending() {
    if (!streamId) return;
    try {
      const res = await fetch(`/api/webrtc/pending/${streamId}/`);
      const data = await res.json();
      if (data.ok) {
        for (const viewerId of data.viewer_ids) {
          if (!peers[viewerId]) {
            await connectToViewer(viewerId);
          }
        }
      }
    } catch (err) {
      console.warn('WebRTCBroadcaster: pending poll failed', err);
    }
  }

  async function connectToViewer(viewerId) {
    const pc = new RTCPeerConnection({ iceServers: ICE_SERVERS });
    peers[viewerId] = { pc, iceSince: 0 };

    localStream.getTracks().forEach((track) => pc.addTrack(track, localStream));

    pc.onicecandidate = (event) => {
      if (event.candidate) {
        window.csrfFetch(`/api/webrtc/ice/${viewerId}/submit/`, {
          method: 'POST',
          body: JSON.stringify({ role: 'broadcaster', candidate: event.candidate }),
        });
      }
    };

    pc.onconnectionstatechange = () => {
      if (['failed', 'closed', 'disconnected'].includes(pc.connectionState)) {
        cleanupPeer(viewerId);
      }
    };

    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);

    await window.csrfFetch(`/api/webrtc/offer/${viewerId}/submit/`, {
      method: 'POST',
      body: JSON.stringify({ sdp: pc.localDescription.sdp }),
    });

    pollForAnswer(viewerId);
    pollForIce(viewerId);
  }

  async function pollForAnswer(viewerId) {
    const entry = peers[viewerId];
    if (!entry) return;
    const check = async () => {
      if (!peers[viewerId]) return;
      try {
        const res = await fetch(`/api/webrtc/answer/${viewerId}/`);
        const data = await res.json();
        if (data.ok && data.ready) {
          await entry.pc.setRemoteDescription({ type: 'answer', sdp: data.sdp });
        } else {
          setTimeout(check, 1500);
        }
      } catch (err) {
        setTimeout(check, 2000);
      }
    };
    check();
  }

  async function pollForIce(viewerId) {
    const entry = peers[viewerId];
    if (!entry) return;
    const check = async () => {
      const current = peers[viewerId];
      if (!current) return;
      try {
        const res = await fetch(`/api/webrtc/ice/${viewerId}/?role=broadcaster&since=${current.iceSince}`);
        const data = await res.json();
        if (data.ok) {
          for (const candidate of data.candidates) {
            try { await current.pc.addIceCandidate(candidate); } catch (e) { /* ignore */ }
          }
          current.iceSince = data.next_index;
        }
      } catch (err) { /* ignore, retry next tick */ }
      if (peers[viewerId]) setTimeout(check, 2000);
    };
    check();
  }

  function cleanupPeer(viewerId) {
    const entry = peers[viewerId];
    if (entry) {
      try { entry.pc.close(); } catch (e) { /* ignore */ }
      delete peers[viewerId];
    }
  }

  return {
    start(newStreamId, newLocalStream, opts = {}) {
      streamId = newStreamId;
      localStream = newLocalStream;
      onViewerCountChange = opts.onViewerCountChange || null;
      pollTimer = setInterval(pollPending, 2000);
      pollPending();
    },
    stop() {
      clearInterval(pollTimer);
      Object.keys(peers).forEach(cleanupPeer);
      streamId = null;
      localStream = null;
    },
  };
})();

/**
 * VIEWER — call connect(streamId, videoEl, callbacks) on the /watch/ page
 * or the OBS Browser Source page.
 */
window.WebRTCViewer = (function () {
  let viewerId = null;
  let pc = null;
  let iceSince = 0;
  let iceTimer = null;

  async function connect(streamId, videoEl, callbacks = {}) {
    const { onConnected, onError, onEnded } = callbacks;

    let joinData;
    try {
      const res = await fetch(`/api/webrtc/join/${streamId}/`, { method: 'POST' });
      joinData = await res.json();
    } catch (err) {
      onError && onError('Could not reach the server.');
      return;
    }

    if (!joinData.ok) {
      onError && onError(joinData.error || 'This stream is not live.');
      return;
    }

    viewerId = joinData.viewer_id;
    pc = new RTCPeerConnection({ iceServers: ICE_SERVERS });

    pc.ontrack = (event) => {
      videoEl.srcObject = event.streams[0];
      onConnected && onConnected();
    };

    pc.onicecandidate = (event) => {
      if (event.candidate) {
        fetch(`/api/webrtc/ice/${viewerId}/submit/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ role: 'viewer', candidate: event.candidate }),
        });
      }
    };

    pc.onconnectionstatechange = () => {
      if (['failed', 'closed', 'disconnected'].includes(pc.connectionState)) {
        onEnded && onEnded();
      }
    };

    pollForOffer();

    window.addEventListener('beforeunload', disconnect);
  }

  async function pollForOffer() {
    if (!viewerId) return;
    try {
      const res = await fetch(`/api/webrtc/offer/${viewerId}/`);
      const data = await res.json();
      if (data.ok && data.ready) {
        await pc.setRemoteDescription({ type: 'offer', sdp: data.sdp });
        const answer = await pc.createAnswer();
        await pc.setLocalDescription(answer);
        await fetch(`/api/webrtc/answer/${viewerId}/submit/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ sdp: pc.localDescription.sdp }),
        });
        pollForIce();
      } else {
        setTimeout(pollForOffer, 1500);
      }
    } catch (err) {
      setTimeout(pollForOffer, 2000);
    }
  }

  function pollForIce() {
    iceTimer = setInterval(async () => {
      if (!viewerId || !pc) return;
      try {
        const res = await fetch(`/api/webrtc/ice/${viewerId}/?role=viewer&since=${iceSince}`);
        const data = await res.json();
        if (data.ok) {
          for (const candidate of data.candidates) {
            try { await pc.addIceCandidate(candidate); } catch (e) { /* ignore */ }
          }
          iceSince = data.next_index;
        }
      } catch (err) { /* ignore, retry next tick */ }
    }, 2000);
  }

  function disconnect() {
    if (viewerId) {
      navigator.sendBeacon && navigator.sendBeacon(`/api/webrtc/leave/${viewerId}/`, new Blob());
    }
    clearInterval(iceTimer);
    if (pc) { try { pc.close(); } catch (e) { /* ignore */ } }
    viewerId = null;
    pc = null;
  }

  return { connect, disconnect };
})();
