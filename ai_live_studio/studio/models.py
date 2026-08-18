import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


def look_image_upload_path(instance, filename):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'jpg'
    return f'looks/{instance.user_id}/{uuid.uuid4().hex}.{ext}'


class Look(models.Model):
    """
    A user-uploaded photo of a target face, used as the reference image
    sent to the face-swap API for real-time video processing (see
    api/stream.py's transform_video()).

    Storage note: these are photos of people's faces used to alter a live
    video stream, so they're treated as sensitive — the file lives under
    MEDIA_ROOT but is only ever served through the login+ownership-checked
    studio.views.look_image_view, never a raw public /media/ URL. Update
    your templates/views accordingly if you change how these are served.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='looks')
    name = models.CharField(max_length=80)
    image = models.ImageField(upload_to=look_image_upload_path)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.user.username})'


class Stream(models.Model):
    """Represents a single AI livestream session."""

    STATUS_CHOICES = [
        ('idle', 'Idle'),
        ('live', 'Live'),
        ('ended', 'Ended'),
        ('error', 'Error'),
    ]

    QUALITY_CHOICES = [
        ('low', 'Low (fast)'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('ultra', 'Ultra (4K)'),
    ]

    RESOLUTION_CHOICES = [
        ('480p', '480p'),
        ('720p', '720p'),
        ('1080p', '1080p'),
        ('4k', '4K'),
    ]

    stream_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='streams')

    title = models.CharField(max_length=200, blank=True, default='Untitled Stream')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='idle')

    # `look` points at the user's uploaded target-face photo (see the Look
    # model below) used for real-time face swapping. `ai_character` is kept
    # only for backward compatibility with the old hardcoded-style-name
    # system and is no longer written to by the studio UI.
    look = models.ForeignKey('studio.Look', on_delete=models.SET_NULL, null=True, blank=True, related_name='streams')
    ai_character = models.CharField(max_length=100, default='default_avatar')
    background = models.CharField(max_length=100, default='none')
    quality = models.CharField(max_length=10, choices=QUALITY_CHOICES, default='medium')
    resolution = models.CharField(max_length=10, choices=RESOLUTION_CHOICES, default='720p')
    camera_device = models.CharField(max_length=150, blank=True, default='')
    microphone_device = models.CharField(max_length=150, blank=True, default='')
    mirrored = models.BooleanField(default=False)
    muted = models.BooleanField(default=False)

    audience_count = models.PositiveIntegerField(default=0)
    peak_audience = models.PositiveIntegerField(default=0)
    credits_used = models.PositiveIntegerField(default=0)

    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.user.username}) - {self.status}'

    @property
    def live_url(self):
        return f'/watch/{self.stream_id}/'

    @property
    def duration_seconds(self):
        if self.started_at and self.ended_at:
            return int((self.ended_at - self.started_at).total_seconds())
        if self.started_at and self.status == 'live':
            return int((timezone.now() - self.started_at).total_seconds())
        return 0

    def start(self):
        self.status = 'live'
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at'])

    def stop(self):
        self.status = 'ended'
        self.ended_at = timezone.now()
        self.save(update_fields=['status', 'ended_at'])


class ChatMessage(models.Model):
    """
    Live chat message on a Stream. Works for both the authenticated
    broadcaster and anonymous viewers (who pick a display name client-side
    on the /watch/ page) — powered by simple HTTP polling, same pattern as
    WebRTCSession's signaling, so no websocket server is required.
    """

    stream = models.ForeignKey(Stream, on_delete=models.CASCADE, related_name='chat_messages')
    display_name = models.CharField(max_length=80)
    message = models.CharField(max_length=500)
    is_broadcaster = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.display_name}: {self.message[:40]}'


class WebRTCSession(models.Model):
    """
    One row per viewer connection to a live Stream. Powers browser-to-browser
    (WebRTC) video delivery using simple HTTP-poll signaling, so no extra
    infrastructure (websocket server, TURN service, etc.) is required to
    demo peer-to-peer streaming out of the box.

    Flow:
      1. Viewer POSTs /api/webrtc/join/<stream_id>/  -> row created, status='pending'
      2. Broadcaster polls /api/webrtc/pending/<stream_id>/ for new rows,
         creates an RTCPeerConnection + offer, POSTs it back -> status='offered'
      3. Viewer polls for the offer, creates an answer, POSTs it back -> status='answered'
      4. Broadcaster polls for the answer and completes the connection.
      5. Both sides trickle ICE candidates through the ice endpoints.

    NOTE: this is a direct browser-to-browser (mesh) connection intended for
    demos, local networks, and small audiences. For large-scale public
    broadcasting you would front this with a proper SFU/media server — the
    signaling contract here is written so that swap is a backend-only change.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('offered', 'Offered'),
        ('answered', 'Answered'),
        ('connected', 'Connected'),
        ('closed', 'Closed'),
    ]

    viewer_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    stream = models.ForeignKey(Stream, on_delete=models.CASCADE, related_name='webrtc_sessions')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='pending')

    offer_sdp = models.TextField(blank=True, default='')
    answer_sdp = models.TextField(blank=True, default='')

    broadcaster_ice = models.JSONField(default=list, blank=True)
    viewer_ice = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Viewer {self.viewer_id} on {self.stream_id} ({self.status})'
