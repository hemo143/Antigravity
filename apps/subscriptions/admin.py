"""
إدارة الباقات والعقود والفواتير من Django Admin — مع فلاتر وبحث.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Package, Contract, Invoice


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'price_monthly', 'price_yearly', 'max_events', 'max_attendees',
                    'commission_rate', 'has_slido', 'has_reports', 'is_popular', 'is_active']
    list_filter = ['is_active', 'is_popular', 'has_slido', 'has_reports']
    list_editable = ['is_popular', 'is_active']
    search_fields = ['name', 'tagline']
    prepopulated_fields = {'slug': ('name',)}


class InvoiceInline(admin.TabularInline):
    model = Invoice
    extra = 0
    readonly_fields = ['number', 'created_at']


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'package', 'payment_method', 'status', 'payment_status',
                    'amount_display', 'start_date', 'end_date', 'created_at']
    list_filter = ['status', 'payment_status', 'payment_method', 'package']
    search_fields = ['company_name', 'contact_email', 'contact_phone']
    date_hierarchy = 'created_at'
    list_editable = ['status', 'payment_status']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [InvoiceInline]
    autocomplete_fields = ['package']

    @admin.display(description='القيمة')
    def amount_display(self, obj):
        return f'{obj.amount} ج.م'


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['number', 'contract', 'amount', 'status', 'issued_date', 'pdf_link']
    list_filter = ['status', 'issued_date']
    search_fields = ['number', 'contract__company_name', 'contract__contact_email']
    date_hierarchy = 'issued_date'
    list_editable = ['status']
    readonly_fields = ['number', 'created_at']

    @admin.display(description='PDF')
    def pdf_link(self, obj):
        from django.urls import reverse
        try:
            url = reverse('subscriptions:invoice_pdf', kwargs={'pk': obj.pk})
            return format_html('<a href="/en{}" target="_blank">PDF ⤓</a>', url)
        except Exception:
            return '—'
