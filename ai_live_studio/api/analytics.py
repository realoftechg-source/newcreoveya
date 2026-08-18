"""
Analytics module. Placeholder hooks for pushing/pulling stream metrics
to/from an external analytics or AI-monitoring provider.
"""


def record_stream_event(stream, event_name, payload=None, **kwargs):
    """
    Called on key stream lifecycle events (started, stopped, viewer
    joined, error, etc). Wire this up to your own analytics pipeline.

    # INSERT MY API HERE
    """
    pass


def push_external_metrics(stream, **kwargs):
    """
    Optional: forward local stream metrics to an external dashboard or
    monitoring service.

    # INSERT MY API HERE
    """
    pass
