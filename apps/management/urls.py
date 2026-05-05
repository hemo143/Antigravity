"""
Management URLs - Supplier & Bill routing
"""
from django.urls import path
from . import views

app_name = 'management'

urlpatterns = [
    # ─── Suppliers ────────────────────────────────────────────────
    path('suppliers/', views.supplier_list_view, name='supplier_list'),
    path('suppliers/create/', views.supplier_create_view, name='supplier_create'),
    path('suppliers/<int:pk>/', views.supplier_detail_view, name='supplier_detail'),
    path('suppliers/<int:pk>/edit/', views.supplier_update_view, name='supplier_update'),
    path('suppliers/<int:pk>/delete/', views.supplier_delete_view, name='supplier_delete'),

    # ─── Bills ────────────────────────────────────────────────────
    path('bills/', views.bill_list_view, name='bill_list'),
    path('bills/create/', views.bill_create_view, name='bill_create'),
    path('bills/<int:pk>/edit/', views.bill_update_view, name='bill_update'),
    path('bills/<int:pk>/delete/', views.bill_delete_view, name='bill_delete'),
]
