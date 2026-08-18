"""
Stream control module.

These functions are intentionally left as placeholders. The platform's
views call into this module rather than performing AI logic directly, so
you can plug in your own AI streaming API here later without touching
any other part of the codebase.
"""

import requests
from django.conf import settings


def get_decart_api_key():
    """Checks the admin-editable PlatformSetting override first (set from
    /admin_dashboard/), falls back to the DECART_API_KEY env var."""
    try:
        from payments.models import PlatformSetting
        override = PlatformSetting.load().decart_api_key_override
        if override:
            return override
    except Exception:
        pass
    return settings.DECART_API_KEY


def is_ai_engine_connected():
    return bool(get_decart_api_key())


def start_ai_stream(stream, **kwargs):
    """
    Called when a user clicks "Start Stream" in AI Studio.

    `stream` is a studio.models.Stream instance that has already been
    marked as 'live' and saved. Use this hook to kick off your own
    AI pipeline / external streaming service.

    # INSERT MY API HERE
    """
    pass


def stop_ai_stream(stream, **kwargs):
    """
    Called when a user clicks "Stop Stream" or the stream ends.

    `stream` is a studio.models.Stream instance that has already been
    marked as 'ended' and saved.

    # INSERT MY API HERE
    """
    pass


def create_realtime_client_token(user, **kwargs):
    """
    ============================================================
    THIS IS WHERE YOUR DECART API KEY GOES.
    ============================================================

    Called once per broadcast session (see api/views.py -> get_realtime_token,
    wired to static/js/decart_realtime.js). Runs server-side only, so your
    permanent DECART_API_KEY never reaches the browser.

    Decart's realtime model doesn't work like a per-frame REST call — the
    browser connects DIRECTLY to Decart via WebRTC for low latency. To make
    that possible without exposing your permanent key client-side, we
    exchange it here for a short-lived client token (10 min TTL, Decart's
    documented pattern) and hand only that token to the browser.

    Returns:
        A dict like {"apiKey": "ek_...", "expiresAt": "..."} to pass to the
        browser, or None if not configured / the exchange fails (caller
        falls back to raw camera passthrough).
    """
    api_key = get_decart_api_key()
    if not api_key:
        return None  # not configured yet — caller passes the raw camera through

    try:
        response = requests.post(
            'https://api.decart.ai/v1/client/tokens',
            headers={
                'x-api-key': api_key,
                'Content-Type': 'application/json',
            },
            json={
                'expiresIn': 600,  # 10 minutes; active sessions keep working past this
                'allowedModels': [settings.DECART_MODEL],
            },
            timeout=settings.FACE_SWAP_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()

    except requests.RequestException:
        return None


def get_stream_status(stream, **kwargs):
    """
    Optional hook to pull live status from an external AI/streaming
    provider instead of relying solely on local DB state.

    # INSERT MY API HERE
    """
    return {
        'status': stream.status,
        'audience_count': stream.audience_count,
        'duration_seconds': stream.duration_seconds,
    }
