"""
Management Admin - تسجيل النماذج في Django Admin
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Supplier, Bill, PortfolioProject, QuoteRequest


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display   = ['name', 'service_type', 'contact_person', 'phone', 'email', 'is_active', 'created_at']
    list_filter    = ['service_type', 'is_active']
    search_fields  = ['name', 'contact_person', 'email']
    list_editable  = ['is_active']
    ordering       = ['name']


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display   = ['title', 'supplier', 'event', 'amount', 'paid_amount', 'status', 'due_date']
    list_filter    = ['status', 'supplier', 'event']
    search_fields  = ['title', 'supplier__name']
    ordering       = ['-due_date']
    date_hierarchy = 'due_date'


@admin.register(PortfolioProject)
class PortfolioProjectAdmin(admin.ModelAdmin):
    list_display   = ['image_preview', 'title_en', 'title_ar', 'event_type', 'is_featured', 'order']
    list_filter    = ['event_type', 'is_featured']
    list_editable  = ['is_featured', 'order']
    search_fields  = ['title_en', 'title_ar']
    readonly_fields = ['image_preview']
    fieldsets = (
        ('English Content', {
            'fields': ('title_en', 'description_en'),
        }),
        ('Arabic Content / المحتوى العربي', {
            'fields': ('title_ar', 'description_ar'),
        }),
        ('Media & Settings', {
            'fields': ('image', 'image_preview', 'event_type', 'is_featured', 'order'),
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:70px;width:110px;object-fit:cover;border-radius:8px;">',
                obj.image.url
            )
        return '—'
    image_preview.short_description = 'Preview'


@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display   = ['name', 'company', 'email', 'phone', 'event_type', 'attendees', 'event_date', 'is_contacted', 'created_at']
    list_filter    = ['event_type', 'is_contacted', 'created_at']
    list_editable  = ['is_contacted']
    search_fields  = ['name', 'company', 'email', 'phone']
    readonly_fields = ['name', 'company', 'email', 'phone', 'event_type', 'attendees', 'event_date', 'services', 'notes', 'created_at']
    ordering       = ['-created_at']
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Contact Info', {
            'fields': ('name', 'company', 'email', 'phone'),
        }),
        ('Event Details', {
            'fields': ('event_type', 'attendees', 'event_date', 'services'),
        }),
        ('Message', {
            'fields': ('notes',),
        }),
        ('Status', {
            'fields': ('is_contacted', 'created_at'),
        }),
    )
