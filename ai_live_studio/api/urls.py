from django.urls import path

from api import views

app_name = 'api'

urlpatterns = [
    path('start-stream/', views.start_stream, name='start_stream'),
    path('stop-stream/', views.stop_stream, name='stop_stream'),
    path('stream-status/', views.stream_status, name='stream_status'),
    path('watch-status/<uuid:stream_id>/', views.public_stream_status, name='public_stream_status'),
    path('change-avatar/', views.change_avatar, name='change_avatar'),
    path('change-camera/', views.change_camera, name='change_camera'),
    path('change-quality/', views.change_quality, name='change_quality'),
    path('change-background/', views.change_background, name='change_background'),

    # WebRTC signaling
    path('webrtc/join/<uuid:stream_id>/', views.webrtc_join, name='webrtc_join'),
    path('webrtc/pending/<uuid:stream_id>/', views.webrtc_pending, name='webrtc_pending'),
    path('webrtc/offer/<uuid:viewer_id>/submit/', views.webrtc_submit_offer, name='webrtc_submit_offer'),
    path('webrtc/offer/<uuid:viewer_id>/', views.webrtc_get_offer, name='webrtc_get_offer'),
    path('webrtc/answer/<uuid:viewer_id>/submit/', views.webrtc_submit_answer, name='webrtc_submit_answer'),
    path('webrtc/answer/<uuid:viewer_id>/', views.webrtc_get_answer, name='webrtc_get_answer'),
    path('webrtc/ice/<uuid:viewer_id>/submit/', views.webrtc_submit_ice, name='webrtc_submit_ice'),
    path('webrtc/ice/<uuid:viewer_id>/', views.webrtc_get_ice, name='webrtc_get_ice'),
    path('webrtc/leave/<uuid:viewer_id>/', views.webrtc_leave, name='webrtc_leave'),

    # Real-time face swap (Decart)
    path('ai/realtime-token/', views.get_realtime_token, name='get_realtime_token'),
    path('ai/current-look/', views.get_current_look, name='get_current_look'),

    # Live chat
    path('chat/<uuid:stream_id>/send/', views.send_chat_message, name='send_chat_message'),
    path('chat/<uuid:stream_id>/messages/', views.get_chat_messages, name='get_chat_messages'),
]
