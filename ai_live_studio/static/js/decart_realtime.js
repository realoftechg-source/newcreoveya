/**
 * Decart real-time face-swap client.
 *
 * Unlike the old per-frame REST approach, this connects the browser
 * DIRECTLY to Decart's realtime servers over WebRTC — Django is only
 * involved to hand out a short-lived token (see api/stream.py's
 * create_realtime_client_token()) and to serve the user's uploaded
 * reference-face image. Actual video frames never touch our backend.
 *
 * SDK loaded on demand via esm.sh (no build step / bundler needed):
 *   https://www.jsdelivr.com/package/npm/@decartai/sdk
 *
 * Note: this wraps the SDK calls documented at
 * https://docs.platform.decart.ai/ as of this build. If Decart changes
 * their SDK's method names (e.g. the exact disconnect/session API),
 * check their JS SDK reference and adjust the marked spots below.
 */

window.DecartRealtime = (function () {
  const DEFAULT_PROMPT =
    'Substitute the character in the video with the person in the reference image.';

  let session = null; // the object returned by client.realtime.connect()

  async function fetchCurrentLook() {
    const res = await fetch('/api/ai/current-look/');
    const data = await res.json();
    return data.ok ? data.look : null;
  }

  async function fetchLookImageBlob(imageUrl) {
    // Same-origin fetch automatically carries the session cookie, so this
    // works even though the look image is served from a login-protected
    // view — no public URL is ever exposed to Decart or anyone else.
    const res = await fetch(imageUrl);
    if (!res.ok) return null;
    return res.blob();
  }

  async function fetchEphemeralToken() {
    const res = await window.csrfFetch('/api/ai/realtime-token/', { method: 'POST' });
    return res.json();
  }

  return {
    /**
     * start(localStream, options) -> MediaStream | null
     *
     * Returns null (caller should fall back to raw camera) if:
     *   - no look is currently selected ("My Camera" / no swap wanted)
     *   - the AI engine isn't configured yet
     *   - the connection fails for any reason
     *
     * options.onStatusChange: (status) => {}
     *   'active' | 'connecting' | 'fallback' | 'disconnected'
     */
    async start(localStream, options = {}) {
      const onStatusChange = options.onStatusChange || (() => {});
      onStatusChange('connecting');

      const look = await fetchCurrentLook();
      if (!look) {
        // "My Camera" selected — nothing to swap to, use raw camera.
        return null;
      }

      const imageBlob = await fetchLookImageBlob(look.image_url);
      if (!imageBlob) {
        console.warn('DecartRealtime: could not load the selected look image.');
        onStatusChange('fallback');
        return null;
      }

      const tokenData = await fetchEphemeralToken();
      if (!tokenData.ok) {
        console.warn('DecartRealtime: could not get a realtime token —', tokenData.error);
        onStatusChange('fallback');
        return null;
      }

      let createDecartClient, models;
      try {
        ({ createDecartClient, models } = await import('https://esm.sh/@decartai/sdk'));
      } catch (err) {
        console.warn('DecartRealtime: failed to load the Decart SDK.', err);
        onStatusChange('fallback');
        return null;
      }

      const client = createDecartClient({ apiKey: tokenData.token.apiKey });
      const model = models.realtime(tokenData.model);

      return new Promise((resolve) => {
        let settled = false;

        client.realtime
          .connect(localStream, {
            model,
            mirror: 'auto',
            onRemoteStream: (remoteStream) => {
              // Decart transforms video only — keep the original mic audio.
              const combined = new MediaStream([
                ...remoteStream.getVideoTracks(),
                ...localStream.getAudioTracks(),
              ]);
              onStatusChange('active');
              if (!settled) {
                settled = true;
                resolve(combined);
              }
            },
            onError: (err) => {
              console.warn('DecartRealtime: connection error —', err);
              onStatusChange('fallback');
              if (!settled) {
                settled = true;
                resolve(null);
              }
            },
            onDisconnect: (reason) => {
              console.log('DecartRealtime: disconnected —', reason);
              onStatusChange('disconnected');
            },
            initialState: {
              prompt: { text: DEFAULT_PROMPT, enhance: true },
              image: imageBlob,
            },
          })
          .then((activeSession) => {
            session = activeSession;
          })
          .catch((err) => {
            console.warn('DecartRealtime: connect() failed —', err);
            onStatusChange('fallback');
            if (!settled) {
              settled = true;
              resolve(null);
            }
          });
      });
    },

    stop() {
      if (session && typeof session.disconnect === 'function') {
        try {
          session.disconnect();
        } catch (err) {
          console.warn('DecartRealtime: error during disconnect —', err);
        }
      }
      session = null;
    },

    isActive() {
      return !!session;
    },
  };
})();
