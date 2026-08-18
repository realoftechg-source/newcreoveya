from django.urls import path

from admin_dashboard import views

app_name = 'admin_dashboard'

urlpatterns = [
    path('', views.overview_view, name='overview'),

    path('users/', views.users_view, name='users'),
    path('users/create/', views.create_user_view, name='create_user'),
    path('users/<int:user_id>/credits/', views.edit_user_credits_view, name='edit_user_credits'),
    path('users/<int:user_id>/suspend/', views.suspend_user_view, name='suspend_user'),
    path('users/<int:user_id>/delete/', views.delete_user_view, name='delete_user'),

    path('plans/', views.plans_view, name='plans'),
    path('plans/save/', views.save_plan_view, name='save_plan'),
    path('plans/<int:plan_id>/save/', views.save_plan_view, name='save_plan_edit'),
    path('plans/<int:plan_id>/delete/', views.delete_plan_view, name='delete_plan'),

    path('payment-methods/', views.payment_methods_view, name='payment_methods'),
    path('payment-methods/save/', views.save_payment_method_view, name='save_payment_method'),
    path('payment-methods/<int:method_id>/save/', views.save_payment_method_view, name='save_payment_method_edit'),
    path('payment-methods/<int:method_id>/delete/', views.delete_payment_method_view, name='delete_payment_method'),

    path('payments/', views.payment_submissions_view, name='payment_submissions'),
    path('payments/<int:submission_id>/approve/', views.approve_payment_view, name='approve_payment'),
    path('payments/<int:submission_id>/reject/', views.reject_payment_view, name='reject_payment'),

    path('settings/', views.platform_settings_view, name='platform_settings'),
    path('settings/save/', views.save_platform_settings_view, name='save_platform_settings'),
]
