"""
Events URL Configuration
"""
from django.urls import path
from . import views, api_views

app_name = 'events'

urlpatterns = [
    # Public
    path('', views.event_list_view, name='event_list'),
    # Eventbrite + Slido (لازم قبل المسار العام <slug>/ عشان ما يتلقفش)
    path('eventbrite/', views.eventbrite_events_view, name='eventbrite_events'),
    path('<slug:slug>/', views.event_detail_view, name='event_detail'),
    path('<slug:slug>/live/', views.event_live_view, name='event_live'),

    # Booking
    path('<slug:slug>/book/', views.book_event_view, name='book_event'),
    path('bookings/my/', views.my_bookings_view, name='my_bookings'),
    path('bookings/<int:booking_id>/cancel/', views.cancel_booking_view, name='cancel_booking'),

    # Management
    path('manage/create/', views.event_create_view, name='event_create'),
    path('manage/<slug:slug>/edit/', views.event_update_view, name='event_update'),
    path('manage/<slug:slug>/delete/', views.event_delete_view, name='event_delete'),

    # Categories
    path('categories/', views.category_list_view, name='category_list'),
    path('categories/create/', views.category_create_view, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_update_view, name='category_update'),
    path('categories/<int:pk>/delete/', views.category_delete_view, name='category_delete'),

    # API v1
    path('api/v1/list/', api_views.EventListView.as_view(), name='api_event_list'),
    path('api/v1/<slug:slug>/', api_views.EventDetailView.as_view(), name='api_event_detail'),
    path('api/v1/categories/', api_views.CategoryListView.as_view(), name='api_category_list'),
    path('api/v1/<slug:slug>/book/', api_views.BookEventAPI.as_view(), name='api_book_event'),
    # WishList
    path('wishlist/', views.wishlist_list_view, name='wishlist_list'),
    path('wishlist/toggle/<slug:slug>/', views.toggle_wishlist_view, name='toggle_wishlist'),

    # Attendee Management
    path('event/<slug:slug>/attendees/', views.event_attendees_view, name='event_attendees'),
    path('booking/<int:booking_id>/mark-attendance/', views.mark_attendance_view, name='mark_attendance'),
]
