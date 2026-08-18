from django.urls import path

from dashboard import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('settings/', views.settings_view, name='settings'),
    path('tutorial/', views.tutorial_view, name='tutorial'),
    path('feed/', views.feed_view, name='feed'),
    path('ai-jobs/', views.ai_jobs_view, name='ai_jobs'),
]
