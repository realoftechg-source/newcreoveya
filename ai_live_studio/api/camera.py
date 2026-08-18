"""
Camera / device control module. Placeholder hooks for wiring up custom
camera or capture-device logic (e.g. server-side device validation,
hardware-accelerated capture, etc).
"""


def change_camera(stream, device_id, **kwargs):
    """
    Called when the user switches their camera device in AI Studio.

    # INSERT MY API HERE
    """
    stream.camera_device = device_id
    stream.save(update_fields=['camera_device'])
    return {'camera_device': stream.camera_device}


def change_microphone(stream, device_id, **kwargs):
    """
    Called when the user switches their microphone device.

    # INSERT MY API HERE
    """
    stream.microphone_device = device_id
    stream.save(update_fields=['microphone_device'])
    return {'microphone_device': stream.microphone_device}


def toggle_mirror(stream, **kwargs):
    """Flip the mirror state for the local camera preview."""
    stream.mirrored = not stream.mirrored
    stream.save(update_fields=['mirrored'])
    return {'mirrored': stream.mirrored}


def toggle_mute(stream, **kwargs):
    """Mute/unmute the stream's microphone."""
    stream.muted = not stream.muted
    stream.save(update_fields=['muted'])
    return {'muted': stream.muted}
