"""
API URL Configuration - Django REST Framework
"""
from django.urls import path
from . import api_views

app_name = 'api'

urlpatterns = [
    # Categories
    path('categories/', api_views.CategoryListView.as_view(), name='category_list'),
    path('categories/<int:pk>/', api_views.CategoryDetailView.as_view(), name='category_detail'),

    # Events
    path('events/', api_views.EventListView.as_view(), name='event_list'),
    path('events/<slug:slug>/', api_views.EventDetailView.as_view(), name='event_detail'),

    # Bookings
    path('bookings/', api_views.BookingListView.as_view(), name='booking_list'),
    path('bookings/<int:pk>/', api_views.BookingDetailView.as_view(), name='booking_detail'),

    # Stats
    path('stats/', api_views.dashboard_stats, name='stats'),
]
