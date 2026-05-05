from django.contrib import admin
from .models import Event, Category, Booking


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'get_events_count', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


class BookingInline(admin.TabularInline):
    model = Booking
    extra = 0
    readonly_fields = ['user', 'tickets', 'total_price', 'status', 'booked_at']


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'organizer', 'start_date', 'status', 'available_seats', 'is_featured']
    list_filter = ['status', 'category', 'is_free', 'is_featured', 'is_online']
    search_fields = ['title', 'venue', 'city']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'start_date'
    ordering = ['-start_date']
    inlines = [BookingInline]
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'slug', 'description', 'short_description', 'cover_image', 'category', 'organizer')
        }),
        ('Date & Location', {
            'fields': ('start_date', 'end_date', 'venue', 'venue_address', 'city', 'is_online', 'online_link')
        }),
        ('Tickets & Pricing', {
            'fields': ('capacity', 'price', 'is_free')
        }),
        ('Status', {
            'fields': ('status', 'is_featured', 'created_at', 'updated_at')
        }),
    )


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['user', 'event', 'status', 'tickets', 'total_price', 'booked_at']
    list_filter = ['status', 'event__category']
    search_fields = ['user__email', 'event__title']
    date_hierarchy = 'booked_at'
    readonly_fields = ['total_price', 'booked_at']
