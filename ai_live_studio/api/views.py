import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_GET, require_POST

from api import avatar as avatar_api
from api import camera as camera_api
from api import credits as credits_api
from api import stream as stream_api
from api import webrtc as webrtc_api
from core.utils import log_activity
from studio.models import Stream, WebRTCSession, Look


def _get_current_stream(user):
    """
    The user's current studio session — idle (previewing, not live yet) or
    live. Look/camera/background changes apply to this regardless of
    whether they've gone live, so switching your AI character works during
    preview, not just mid-stream.
    """
    return Stream.objects.filter(user=user, status__in=['idle', 'live']).order_by('-created_at').first()


def _get_or_create_current_stream(user):
    stream = _get_current_stream(user)
    if stream:
        return stream
    return Stream.objects.create(user=user, status='idle')


def _parse_json(request):
    if request.body:
        try:
            return json.loads(request.body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}
    return request.POST.dict()


# ---------------------------------------------------------------------------
# Stream lifecycle
# ---------------------------------------------------------------------------

@login_required
@require_POST
@csrf_protect
def start_stream(request):
    data = _parse_json(request)
    user = request.user

    stream = _get_current_stream(user)
    if stream and stream.status == 'live':
        return JsonResponse({'ok': False, 'error': 'A stream is already live.'}, status=400)

    if not user.has_enough_credits(1):
        return JsonResponse({'ok': False, 'error': 'Not enough credits to start a stream.'}, status=402)

    if not stream:
        stream = Stream.objects.create(user=user, status='idle')

    stream.title = data.get('title', stream.title or 'Untitled Stream')
    stream.background = data.get('background', stream.background)
    stream.quality = data.get('quality', stream.quality)
    stream.resolution = data.get('resolution', stream.resolution)
    stream.camera_device = data.get('camera_device', stream.camera_device)
    stream.microphone_device = data.get('microphone_device', stream.microphone_device)
    stream.save()
    stream.start()

    # Hand off to the pluggable AI module (placeholder).
    stream_api.start_ai_stream(stream)

    log_activity(request, user, 'stream_start', f'Stream {stream.stream_id} started')

    return JsonResponse({
        'ok': True,
        'stream_id': str(stream.stream_id),
        'status': stream.status,
        'live_url': stream.live_url,
        'started_at': stream.started_at.isoformat(),
    })


@login_required
@require_POST
@csrf_protect
def stop_stream(request):
    stream = Stream.objects.filter(user=request.user, status='live').first()
    if not stream:
        return JsonResponse({'ok': False, 'error': 'No active stream found.'}, status=404)

    stream.stop()
    stream_api.stop_ai_stream(stream)

    # Close out any still-open viewer signaling sessions.
    WebRTCSession.objects.filter(stream=stream).exclude(status='closed').update(status='closed')

    # Deduct credits for the session duration (placeholder pricing model).
    minutes = max(1, stream.duration_seconds // 60)
    cost = credits_api.calculate_stream_cost(stream.quality, minutes)
    credits_api.charge_user(request.user, min(cost, request.user.credits))
    stream.credits_used = cost
    stream.save(update_fields=['credits_used'])

    log_activity(request, request.user, 'stream_stop', f'Stream {stream.stream_id} stopped')

    return JsonResponse({
        'ok': True,
        'stream_id': str(stream.stream_id),
        'status': stream.status,
        'duration_seconds': stream.duration_seconds,
        'credits_used': stream.credits_used,
        'remaining_credits': request.user.credits,
    })


@login_required
@require_GET
def stream_status(request):
    stream = _get_current_stream(request.user)
    if not stream:
        return JsonResponse({'ok': True, 'status': 'idle'})

    status_payload = stream_api.get_stream_status(stream)
    return JsonResponse({
        'ok': True,
        **status_payload,
        'stream_id': str(stream.stream_id),
        'live_url': stream.live_url,
    })


@require_GET
def public_stream_status(request, stream_id):
    """Unauthenticated status check used by the public /watch/ page."""
    stream = Stream.objects.filter(stream_id=stream_id).select_related('user').first()
    if not stream:
        return JsonResponse({'ok': False, 'error': 'Stream not found.'}, status=404)

    return JsonResponse({
        'ok': True,
        'status': stream.status,
        'title': stream.title,
        'streamer': stream.user.display_name,
        'audience_count': stream.audience_count,
        'duration_seconds': stream.duration_seconds,
    })


# ---------------------------------------------------------------------------
# Device / AI character / background controls (work pre-live and live)
# ---------------------------------------------------------------------------

@login_required
@require_POST
@csrf_protect
def change_avatar(request):
    stream = _get_or_create_current_stream(request.user)
    data = _parse_json(request)
    look_id = data.get('look_id')

    look = None
    if look_id:
        # Switching TO a face-swap look (not back to "My Camera") requires
        # credits — this is the "streaming locked until you top up" rule.
        if not request.user.has_enough_credits(1):
            return JsonResponse({
                'ok': False,
                'error': 'Out of credits. Buy more to switch your look or go live again.',
                'code': 'no_credits',
            }, status=402)
        look = Look.objects.filter(pk=look_id, user=request.user).first()
        if not look:
            return JsonResponse({'ok': False, 'error': 'Look not found.'}, status=404)

    result = avatar_api.change_avatar(stream, look)
    return JsonResponse({'ok': True, **result})


@login_required
@require_POST
@csrf_protect
def change_camera(request):
    stream = _get_or_create_current_stream(request.user)
    data = _parse_json(request)
    device_id = data.get('camera_device')
    result = camera_api.change_camera(stream, device_id)
    return JsonResponse({'ok': True, **result})


@login_required
@require_POST
@csrf_protect
def change_quality(request):
    stream = _get_or_create_current_stream(request.user)
    data = _parse_json(request)
    quality = data.get('quality')
    resolution = data.get('resolution')

    if quality:
        stream.quality = quality
    if resolution:
        stream.resolution = resolution
    stream.save(update_fields=['quality', 'resolution'])

    return JsonResponse({'ok': True, 'quality': stream.quality, 'resolution': stream.resolution})


@login_required
@require_POST
@csrf_protect
def change_background(request):
    stream = _get_or_create_current_stream(request.user)
    data = _parse_json(request)
    background_id = data.get('background')
    result = avatar_api.change_background(stream, background_id)
    return JsonResponse({'ok': True, **result})


# ---------------------------------------------------------------------------
# WebRTC signaling (browser-to-browser live delivery for /watch/ and OBS)
# ---------------------------------------------------------------------------

@csrf_exempt
@require_POST
def webrtc_join(request, stream_id):
    """
    A viewer wants to watch. Public — no login, and no CSRF token, since
    anonymous viewers never have a session cookie to carry one. Protected
    instead by the unguessable viewer_id issued here, the same pattern a
    public webhook endpoint would use.
    """
    stream = Stream.objects.filter(stream_id=stream_id, status='live').first()
    if not stream:
        return JsonResponse({'ok': False, 'error': 'This stream is not live.'}, status=404)

    session = webrtc_api.create_viewer_session(stream)

    stream.audience_count += 1
    stream.peak_audience = max(stream.peak_audience, stream.audience_count)
    stream.save(update_fields=['audience_count', 'peak_audience'])

    return JsonResponse({'ok': True, 'viewer_id': str(session.viewer_id)})


@login_required
@require_GET
def webrtc_pending(request, stream_id):
    """Broadcaster polls this for viewers waiting on an offer."""
    stream = get_object_or_404(Stream, stream_id=stream_id, user=request.user)
    sessions = webrtc_api.get_pending_sessions(stream)
    return JsonResponse({'ok': True, 'viewer_ids': [str(s.viewer_id) for s in sessions]})


@login_required
@require_POST
@csrf_protect
def webrtc_submit_offer(request, viewer_id):
    """Broadcaster submits an SDP offer for a specific viewer."""
    session = get_object_or_404(WebRTCSession, viewer_id=viewer_id, stream__user=request.user)
    data = _parse_json(request)
    webrtc_api.submit_offer(session, data.get('sdp', ''))
    return JsonResponse({'ok': True})


@require_GET
def webrtc_get_offer(request, viewer_id):
    """Viewer polls for their offer. Public — identified only by viewer_id."""
    session = get_object_or_404(WebRTCSession, viewer_id=viewer_id)
    if not session.offer_sdp:
        return JsonResponse({'ok': True, 'ready': False})
    return JsonResponse({'ok': True, 'ready': True, 'sdp': session.offer_sdp})


@csrf_exempt
@require_POST
def webrtc_submit_answer(request, viewer_id):
    """Viewer submits their SDP answer. Public — anonymous, no CSRF cookie."""
    session = get_object_or_404(WebRTCSession, viewer_id=viewer_id)
    data = _parse_json(request)
    webrtc_api.submit_answer(session, data.get('sdp', ''))
    return JsonResponse({'ok': True})


@login_required
@require_GET
def webrtc_get_answer(request, viewer_id):
    """Broadcaster polls for the viewer's answer."""
    session = get_object_or_404(WebRTCSession, viewer_id=viewer_id, stream__user=request.user)
    if not session.answer_sdp:
        return JsonResponse({'ok': True, 'ready': False})
    return JsonResponse({'ok': True, 'ready': True, 'sdp': session.answer_sdp})


@csrf_exempt
@require_POST
def webrtc_submit_ice(request, viewer_id):
    """
    Either side submits an ICE candidate. Body: {"role": "broadcaster"|"viewer", "candidate": {...}}
    CSRF-exempt because viewers are anonymous (no cookie to carry a token);
    broadcaster requests are still verified by session ownership below.
    """
    session = get_object_or_404(WebRTCSession, viewer_id=viewer_id)
    data = _parse_json(request)
    role = data.get('role')
    candidate = data.get('candidate')

    if role == 'broadcaster':
        if not request.user.is_authenticated or session.stream.user_id != request.user.id:
            return JsonResponse({'ok': False, 'error': 'Not authorized.'}, status=403)
    elif role != 'viewer':
        return JsonResponse({'ok': False, 'error': 'Invalid role.'}, status=400)

    webrtc_api.add_ice_candidate(session, role, candidate)
    return JsonResponse({'ok': True})


@require_GET
def webrtc_get_ice(request, viewer_id):
    """
    Poll for ICE candidates from the *other* side. Query params:
    role=broadcaster|viewer (who's asking), since=<int> (index already have).
    """
    session = get_object_or_404(WebRTCSession, viewer_id=viewer_id)
    role = request.GET.get('role')
    since = int(request.GET.get('since', 0))

    if role == 'broadcaster' and (not request.user.is_authenticated or session.stream.user_id != request.user.id):
        return JsonResponse({'ok': False, 'error': 'Not authorized.'}, status=403)

    candidates = webrtc_api.get_ice_candidates(session, role, since)
    return JsonResponse({'ok': True, 'candidates': candidates, 'next_index': since + len(candidates)})


@csrf_exempt
@require_POST
def webrtc_leave(request, viewer_id):
    """Viewer disconnects. Public — anonymous, called via sendBeacon on tab close."""
    session = WebRTCSession.objects.filter(viewer_id=viewer_id).first()
    if not session:
        return JsonResponse({'ok': True})

    webrtc_api.close_session(session)

    stream = session.stream
    stream.audience_count = max(0, stream.audience_count - 1)
    stream.save(update_fields=['audience_count'])

    return JsonResponse({'ok': True})


# ---------------------------------------------------------------------------
# Real-time face swap (Decart WebRTC pipeline)
# ---------------------------------------------------------------------------

@login_required
@require_POST
@csrf_protect
def get_realtime_token(request):
    """
    Called by static/js/decart_realtime.js right before the browser opens
    its WebRTC connection to Decart. Only the authenticated broadcaster can
    call this — never exposed to viewers or the public.

    Returns a short-lived Decart client token — never your permanent key.
    The browser uses this token to connect directly to Decart's realtime
    servers, so video frames never round-trip through Django at all (that's
    what makes this fast enough for live video).
    """
    if not stream_api.is_ai_engine_connected():
        return JsonResponse({'ok': False, 'error': 'AI engine not configured yet.'}, status=503)

    token = stream_api.create_realtime_client_token(request.user)
    if not token:
        return JsonResponse({'ok': False, 'error': 'Could not get a realtime token.'}, status=502)

    return JsonResponse({'ok': True, 'token': token, 'model': settings.DECART_MODEL})


@login_required
@require_GET
def get_current_look(request):
    """
    Tells the browser which uploaded Look (if any) is currently selected,
    so decart_realtime.js knows whether/what reference face to send to
    Decart when opening the connection.
    """
    stream = _get_current_stream(request.user)
    look = stream.look if stream else None

    if not look:
        return JsonResponse({'ok': True, 'look': None})

    return JsonResponse({
        'ok': True,
        'look': {
            'id': look.id,
            'name': look.name,
            'image_url': reverse('studio:look_image', args=[look.id]),
        },
    })


# ---------------------------------------------------------------------------
# Live chat (works for the broadcaster and anonymous viewers)
# ---------------------------------------------------------------------------

MAX_CHAT_MESSAGE_LENGTH = 500
MAX_DISPLAY_NAME_LENGTH = 40


@csrf_exempt
@require_POST
def send_chat_message(request, stream_id):
    """
    Public — both the broadcaster (authenticated) and anonymous viewers
    can send chat messages. Viewers pick a display name client-side;
    there's no account required to chat, same as most live platforms'
    guest chat.
    """
    stream = Stream.objects.filter(stream_id=stream_id, status='live').first()
    if not stream:
        return JsonResponse({'ok': False, 'error': 'This stream is not live.'}, status=404)

    data = _parse_json(request)
    message_text = data.get('message', '').strip()[:MAX_CHAT_MESSAGE_LENGTH]
    if not message_text:
        return JsonResponse({'ok': False, 'error': 'Message cannot be empty.'}, status=400)

    is_broadcaster = request.user.is_authenticated and stream.user_id == request.user.id
    if is_broadcaster:
        display_name = request.user.display_name
    else:
        display_name = (data.get('display_name', '').strip() or 'Guest')[:MAX_DISPLAY_NAME_LENGTH]

    from studio.models import ChatMessage
    chat_message = ChatMessage.objects.create(
        stream=stream,
        display_name=display_name,
        message=message_text,
        is_broadcaster=is_broadcaster,
    )

    return JsonResponse({'ok': True, 'id': chat_message.id})


@require_GET
def get_chat_messages(request, stream_id):
    """Public poll endpoint — returns messages newer than ?since=<id>."""
    from studio.models import ChatMessage
    since = int(request.GET.get('since', 0))

    messages_qs = ChatMessage.objects.filter(stream__stream_id=stream_id, id__gt=since)[:100]
    messages_data = [
        {
            'id': m.id,
            'display_name': m.display_name,
            'message': m.message,
            'is_broadcaster': m.is_broadcaster,
            'created_at': m.created_at.strftime('%H:%M'),
        }
        for m in messages_qs
    ]
    next_since = messages_data[-1]['id'] if messages_data else since

    return JsonResponse({'ok': True, 'messages': messages_data, 'next_since': next_since})
