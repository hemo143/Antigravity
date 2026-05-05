from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'first_name', 'last_name', 'role', 'is_verified', 'created_at']
    list_filter = ['role', 'is_verified', 'is_staff', 'is_active']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-created_at']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Extra Info', {'fields': ('role', 'phone', 'bio', 'avatar', 'is_verified')}),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Extra Info', {'fields': ('email', 'role', 'phone')}),
    )
