from django.urls import path

from studio import views

app_name = 'studio'

urlpatterns = [
    path('', views.studio_view, name='home'),
    path('ai-obs/', views.ai_obs_view, name='ai_obs'),
    path('ai-obs/regenerate/', views.regenerate_obs_url_view, name='regenerate_obs_url'),
    path('looks/upload/', views.upload_look_view, name='upload_look'),
    path('looks/<int:look_id>/delete/', views.delete_look_view, name='delete_look'),
    path('looks/<int:look_id>/image/', views.look_image_view, name='look_image'),
]
