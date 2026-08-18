"""
WebRTC signaling helpers.

This is NOT a pluggable "insert your API" module like the other files in
this package — it's working infrastructure that powers real browser-to-
browser video delivery for the /watch/ page and the OBS Browser Source
page, using simple HTTP polling instead of a websocket/media server.
"""

from studio.models import Stream, WebRTCSession


def create_viewer_session(stream):
    """A viewer has requested to watch. Create a pending signaling row."""
    return WebRTCSession.objects.create(stream=stream, status='pending')


def get_pending_sessions(stream):
    """Broadcaster polls this to find viewers waiting for an offer."""
    return WebRTCSession.objects.filter(stream=stream, status='pending')


def submit_offer(session, sdp):
    session.offer_sdp = sdp
    session.status = 'offered'
    session.save(update_fields=['offer_sdp', 'status', 'updated_at'])


def submit_answer(session, sdp):
    session.answer_sdp = sdp
    session.status = 'answered'
    session.save(update_fields=['answer_sdp', 'status', 'updated_at'])


def add_ice_candidate(session, role, candidate):
    """role is 'broadcaster' or 'viewer' — whichever side is submitting."""
    field = 'broadcaster_ice' if role == 'broadcaster' else 'viewer_ice'
    candidates = getattr(session, field)
    candidates.append(candidate)
    setattr(session, field, candidates)
    session.save(update_fields=[field, 'updated_at'])


def get_ice_candidates(session, role, since=0):
    """
    Get candidates submitted by the *other* side. role here is the
    requester's role — so a viewer requesting wants broadcaster_ice, and
    vice versa.
    """
    field = 'viewer_ice' if role == 'broadcaster' else 'broadcaster_ice'
    candidates = getattr(session, field)
    return candidates[since:]


def close_session(session):
    session.status = 'closed'
    session.save(update_fields=['status', 'updated_at'])
