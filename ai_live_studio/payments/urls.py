from django.urls import path

from payments import views

app_name = 'payments'

urlpatterns = [
    path('gate/', views.payment_gate_view, name='gate'),
    path('gate/submit/', views.submit_payment_view, name='submit'),
    path('receipt/<int:submission_id>/', views.receipt_image_view, name='receipt_image'),
    path('credits/', views.credits_view, name='credits'),
    path('', views.billing_view, name='billing'),
    path('transactions/', views.transactions_view, name='transactions'),
]
