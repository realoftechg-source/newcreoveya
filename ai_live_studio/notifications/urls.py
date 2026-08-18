from django.urls import path

from notifications import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notifications_view, name='home'),
    path('mark-all-read/', views.mark_all_read_view, name='mark_all_read'),
    path('<int:pk>/mark-read/', views.mark_read_view, name='mark_read'),
    path('<int:pk>/delete/', views.delete_notification_view, name='delete'),
]
