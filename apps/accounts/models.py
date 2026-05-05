"""
Accounts Models - Custom User Model
نستخدم AbstractUser لإضافة حقول مخصصة للمستخدم الافتراضي في Django
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User Model - نموذج مستخدم مخصص
    يرث من AbstractUser ليحتفظ بكل مميزات Django الافتراضية
    ونضيف عليها حقولنا الخاصة
    """
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('organizer', 'Event Organizer'),
        ('attendee', 'Attendee'),
    ]

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='attendee')
    phone = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    @property
    def is_admin(self):
        return self.role == 'admin' or self.is_staff

    @property
    def is_organizer(self):
        return self.role in ['admin', 'organizer'] or self.is_staff

    def get_bookings_count(self):
        return self.bookings.count()
