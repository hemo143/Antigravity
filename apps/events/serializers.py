from rest_framework import serializers
from .models import Event, Category, Booking

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon', 'color']

class EventSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    organizer_name = serializers.ReadOnlyField(source='organizer.username')
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'slug', 'description', 'category', 'category_name',
            'organizer', 'organizer_name', 'start_date', 'end_date',
            'venue', 'is_online', 'capacity', 'price', 'status', 'available_seats'
        ]

class BookingSerializer(serializers.ModelSerializer):
    event_title = serializers.ReadOnlyField(source='event.title')
    user_email = serializers.ReadOnlyField(source='user.email')

    class Meta:
        model = Booking
        fields = ['id', 'user', 'user_email', 'event', 'event_title', 'status', 'tickets', 'booked_at']
