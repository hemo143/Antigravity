"""
Events Models - النماذج الرئيسية للأحداث والحجوزات
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.urls import reverse


class Category(models.Model):
    """فئة الحدث - مثل: مؤتمر، ورشة عمل، حفلة موسيقية"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='bi-calendar-event', help_text='Bootstrap icon class')
    color = models.CharField(max_length=7, default='#007bff', help_text='Hex color code')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('events:event_list') + f'?category={self.slug}'

    def get_events_count(self):
        return self.events.filter(status='published').count()


class Event(models.Model):
    """
    نموذج الحدث الرئيسي
    يحتوي على كل بيانات الحدث من الاسم إلى التاريخ والمكان
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    # المعلومات الأساسية
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    short_description = models.CharField(max_length=300, blank=True)
    cover_image = models.ImageField(upload_to='events/covers/', blank=True, null=True)

    # التصنيف والمنظم
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='events'
    )
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='organized_events'
    )

    # التاريخ والمكان
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    venue = models.CharField(max_length=200)
    venue_address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    is_online = models.BooleanField(default=False)
    online_link = models.URLField(blank=True, null=True)

    # ─── التكامل مع منصات خارجية (Eventbrite + Slido) ───
    eb_event_id = models.CharField(
        max_length=50, blank=True, default='',
        help_text='Eventbrite numeric Event ID — يفعّل زر شراء التذكرة (Embedded Checkout)'
    )
    slido_code = models.CharField(
        max_length=50, blank=True, default='',
        help_text='Slido event code/hash — يفعّل صفحة التفاعل المباشر مع الحضور'
    )

    # التذاكر والسعر
    capacity = models.PositiveIntegerField(default=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_free = models.BooleanField(default=True)

    # الحالة
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False)

    # الوقت
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Event'
        verbose_name_plural = 'Events'
        ordering = ['-start_date']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('events:event_detail', kwargs={'slug': self.slug})

    @property
    def is_upcoming(self):
        return self.start_date > timezone.now()

    @property
    def is_past(self):
        return self.end_date < timezone.now()

    @property
    def available_seats(self):
        booked = self.bookings.filter(status='confirmed').count()
        return self.capacity - booked

    @property
    def is_full(self):
        return self.available_seats <= 0

    @property
    def booking_percentage(self):
        if self.capacity == 0:
            return 0
        booked = self.bookings.filter(status='confirmed').count()
        return int((booked / self.capacity) * 100)

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            import uuid
            self.slug = slugify(self.title) + '-' + str(uuid.uuid4())[:8]
        if self.price == 0:
            self.is_free = True
        # تحديث الحالة تلقائياً إذا انتهى الحدث
        if self.end_date < timezone.now() and self.status == 'published':
            self.status = 'completed'
        super().save(*args, **kwargs)


class Booking(models.Model):
    """
    نموذج الحجز - يربط المستخدم بالحدث
    كل مستخدم يمكنه حجز مقعد في حدث معين
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('attended', 'Attended'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    tickets = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True)
    booked_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'
        ordering = ['-booked_at']
        # منع الحجز المكرر من نفس المستخدم لنفس الحدث
        unique_together = ['user', 'event']

    def __str__(self):
        return f"{self.user.email} → {self.event.title}"

    def save(self, *args, **kwargs):
        # حساب السعر الكلي تلقائياً
        self.total_price = self.event.price * self.tickets
        super().save(*args, **kwargs)


class WishList(models.Model):
    """
    قائمة الأمنيات - تسمح للمستخدم بحفظ الأحداث المهتم بها
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wishlist'
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='wishlisted_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'WishList'
        verbose_name_plural = 'WishLists'
        unique_together = ['user', 'event']

    def __str__(self):
        return f"{self.user.username} - {self.event.title}"
