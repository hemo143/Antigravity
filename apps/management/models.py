"""
Management Models - Supplier, Bill, Portfolio & Quote Requests
"""
from django.db import models
from apps.events.models import Event


class PortfolioProject(models.Model):
    EVENT_TYPE_CHOICES = [
        ('conference', 'Conference / مؤتمر'),
        ('exhibition', 'Exhibition / معرض'),
        ('corporate',  'Corporate / شركات'),
    ]

    title_en       = models.CharField(max_length=200, verbose_name='Title (English)')
    title_ar       = models.CharField(max_length=200, verbose_name='Title (Arabic)')
    description_en = models.CharField(max_length=300, blank=True, verbose_name='Description (English)')
    description_ar = models.CharField(max_length=300, blank=True, verbose_name='Description (Arabic)')
    event_type     = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, default='conference', verbose_name='Event Type')
    image          = models.ImageField(upload_to='portfolio/', verbose_name='Event Photo')
    is_featured    = models.BooleanField(default=True, verbose_name='Show on website')
    order          = models.PositiveIntegerField(default=0, verbose_name='Display order')
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Portfolio Project'
        verbose_name_plural = 'Portfolio Projects'
        ordering            = ['order', '-created_at']

    def __str__(self):
        return self.title_en


class QuoteRequest(models.Model):
    name       = models.CharField(max_length=200, verbose_name='Name')
    company    = models.CharField(max_length=200, verbose_name='Company')
    email      = models.EmailField(verbose_name='Email')
    phone      = models.CharField(max_length=30, verbose_name='Phone')
    event_type = models.CharField(max_length=50, verbose_name='Event Type')
    attendees  = models.CharField(max_length=50, blank=True, verbose_name='Expected Attendees')
    event_date = models.DateField(null=True, blank=True, verbose_name='Event Date')
    services   = models.CharField(max_length=500, blank=True, verbose_name='Services Required')
    notes      = models.TextField(blank=True, verbose_name='Additional Notes')
    is_contacted = models.BooleanField(default=False, verbose_name='Contacted?')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Quote Request'
        verbose_name_plural = 'Quote Requests'
        ordering            = ['-created_at']

    def __str__(self):
        return f"{self.name} — {self.company} ({self.event_type})"


class Supplier(models.Model):
    """
    نموذج المورد - شركات وأفراد يقدمون خدمات للأحداث
    مثل: شركات الكاتيرينج، صوت وضوء، تصوير...
    """
    SERVICE_CHOICES = [
        ('catering', 'Catering'),
        ('audio_visual', 'Audio & Visual'),
        ('photography', 'Photography & Video'),
        ('decoration', 'Decoration'),
        ('security', 'Security'),
        ('transportation', 'Transportation'),
        ('venue', 'Venue'),
        ('marketing', 'Marketing & Printing'),
        ('technology', 'Technology & IT'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=200, verbose_name='Supplier Name')
    service_type = models.CharField(
        max_length=50,
        choices=SERVICE_CHOICES,
        default='other',
        verbose_name='Service Type'
    )
    contact_person = models.CharField(max_length=150, blank=True, verbose_name='Contact Person')
    phone = models.CharField(max_length=30, blank=True, verbose_name='Phone')
    email = models.EmailField(blank=True, verbose_name='Email')
    address = models.TextField(blank=True, verbose_name='Address')
    notes = models.TextField(blank=True, verbose_name='Notes')
    is_active = models.BooleanField(default=True, verbose_name='Active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Supplier'
        verbose_name_plural = 'Suppliers'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_service_type_display()})"

    def get_total_billed(self):
        """مجموع الفواتير لهذا المورد"""
        return self.bills.aggregate(total=models.Sum('amount'))['total'] or 0

    def get_unpaid_bills_count(self):
        """عدد الفواتير غير المدفوعة"""
        return self.bills.filter(status='unpaid').count()


class Bill(models.Model):
    """
    نموذج الفاتورة / المصروف
    يربط المورد بالحدث ويتتبع المدفوعات
    """
    STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]

    # العلاقات
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name='bills',
        verbose_name='Supplier'
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bills',
        verbose_name='Related Event'
    )

    # البيانات المالية
    title = models.CharField(max_length=200, verbose_name='Bill Title / Description')
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Amount'
    )
    paid_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name='Paid Amount'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='unpaid',
        verbose_name='Payment Status'
    )

    # التواريخ
    issue_date = models.DateField(verbose_name='Issue Date')
    due_date = models.DateField(verbose_name='Due Date')

    # ملفات وملاحظات
    receipt = models.FileField(
        upload_to='bills/receipts/',
        blank=True,
        null=True,
        verbose_name='Receipt / Invoice File'
    )
    notes = models.TextField(blank=True, verbose_name='Notes')

    # التوقيت
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Bill'
        verbose_name_plural = 'Bills'
        ordering = ['-due_date']

    def __str__(self):
        return f"{self.title} — {self.supplier.name} ({self.get_status_display()})"

    @property
    def remaining_amount(self):
        return self.amount - self.paid_amount

    @property
    def is_overdue(self):
        from django.utils import timezone
        return self.due_date < timezone.now().date() and self.status in ['unpaid', 'partial']

    def save(self, *args, **kwargs):
        # تحديث الحالة تلقائياً بناء على المبلغ المدفوع
        if self.paid_amount >= self.amount:
            self.status = 'paid'
        elif self.paid_amount > 0:
            self.status = 'partial'
        elif self.status not in ['cancelled']:
            self.status = 'unpaid'
        super().save(*args, **kwargs)
