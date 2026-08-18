"""
AI character / avatar & background module. change_avatar() now points a
Stream at a real, user-uploaded target-face photo (see studio.models.Look)
rather than a hardcoded style label. The background list below is a
separate, unrelated concept (virtual/blurred backgrounds) and is still a
simple placeholder list.
"""

AVAILABLE_BACKGROUNDS = [
    {'id': 'none', 'name': 'None (camera background)'},
    {'id': 'blur', 'name': 'Blur'},
    {'id': 'office', 'name': 'Modern Office'},
    {'id': 'studio', 'name': 'Studio Backdrop'},
    {'id': 'gradient_purple', 'name': 'Purple Gradient'},
    {'id': 'custom_upload', 'name': 'Custom Upload'},
]


def change_avatar(stream, look, **kwargs):
    """
    Called when the user switches their "look" in AI Studio.

    `look` is a studio.models.Look instance (the user's uploaded target-face
    photo) or None to turn face-swapping off and stream the raw camera.

    This just records the selection — the actual image gets read and sent
    to your face-swap API per-frame in api/stream.py's transform_video(),
    since that's where the real API call happens.
    """
    stream.look = look
    stream.save(update_fields=['look'])
    return {'look_id': look.id if look else None, 'look_name': look.name if look else None}


def change_background(stream, background_id, **kwargs):
    """
    Called when the user switches the AI-rendered background.

    # INSERT MY AI API HERE
    """
    stream.background = background_id
    stream.save(update_fields=['background'])
    return {'background': stream.background}
