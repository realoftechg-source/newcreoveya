from django.urls import path

from core import pages_views

app_name = 'pages'

urlpatterns = [
    path('cookies/', pages_views.cookies_view, name='cookies'),
    path('contact/', pages_views.contact_view, name='contact'),
    path('terms/', pages_views.terms_view, name='terms'),
    path('privacy/', pages_views.privacy_view, name='privacy'),
    path('disclaimer/', pages_views.disclaimer_view, name='disclaimer'),
    path('refund-policy/', pages_views.refund_policy_view, name='refund_policy'),
]
