"""
URLs نظام الباقات والتعاقد.
"""
from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    path('pricing/', views.pricing_view, name='pricing'),
    path('contract/', views.contract_view, name='contract'),
    path('contract/thanks/', views.contract_thanks_view, name='contract_thanks'),
    path('portal/', views.client_dashboard_view, name='dashboard'),
    path('invoice/<int:pk>/', views.invoice_detail_view, name='invoice_detail'),
    path('invoice/<int:pk>/pdf/', views.invoice_pdf_view, name='invoice_pdf'),
]
