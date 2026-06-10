"""
نماذج نظام الباقات والتعاقد:
- Package : باقة خدمة (أساسي / احترافي / VIP)
- Contract: عقد بين منظّم/شركة وباقة معيّنة
- Invoice : فاتورة مرتبطة بعقد
"""
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class Package(models.Model):
    """باقة خدمة معروضة في صفحة الأسعار."""
    TIER_CHOICES = [
        ('basic', 'أساسي'),
        ('pro', 'احترافي'),
        ('vip', 'VIP'),
    ]

    name = models.CharField('اسم الباقة', max_length=50, choices=TIER_CHOICES, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    tagline = models.CharField('وصف مختصر', max_length=160, blank=True)

    # الأسعار
    price_monthly = models.DecimalField('السعر الشهري', max_digits=10, decimal_places=2, default=0)
    price_yearly = models.DecimalField('السعر السنوي', max_digits=10, decimal_places=2, default=0,
                                       help_text='عادةً بخصم 20% عن (الشهري × 12)')

    # الحدود
    max_events = models.PositiveIntegerField('عدد الفعاليات المسموح بيها', default=1)
    max_attendees = models.PositiveIntegerField('عدد الحضور المسموح بيه', default=100)
    commission_rate = models.DecimalField('نسبة العمولة على التذاكر %', max_digits=5, decimal_places=2,
                                          default=Decimal('5.00'))

    # المميزات والخصائص
    features = models.JSONField('المميزات', default=list, blank=True,
                                help_text='قائمة نصية، كل عنصر ميزة. مثال: ["دعم فني", "صفحة فعالية مخصّصة"]')
    has_slido = models.BooleanField('تتضمّن Slido؟', default=False)
    has_reports = models.BooleanField('تتضمّن تقارير؟', default=False)

    # العرض
    is_popular = models.BooleanField('الأكثر طلبًا (مميّزة)', default=False)
    is_active = models.BooleanField('مفعّلة', default=True)
    sort_order = models.PositiveIntegerField('الترتيب', default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Package'
        verbose_name_plural = 'Packages'
        ordering = ['sort_order', 'price_monthly']

    def __str__(self):
        return self.get_name_display()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('subscriptions:contract') + f'?package={self.slug}'

    @property
    def yearly_discount_percent(self):
        """نسبة التوفير في الاشتراك السنوي مقارنةً بالشهري × 12."""
        full = self.price_monthly * 12
        if full <= 0:
            return 0
        return int(round((full - self.price_yearly) / full * 100))

    @property
    def yearly_monthly_equivalent(self):
        """السعر السنوي مقسومًا على 12 (للعرض كـ 'يعادل شهريًا')."""
        return (self.price_yearly / 12).quantize(Decimal('0.01')) if self.price_yearly else Decimal('0')


class Contract(models.Model):
    """عقد اشتراك بين شركة/منظّم وباقة."""
    STATUS_CHOICES = [
        ('pending', 'قيد المراجعة'),
        ('active', 'نشط'),
        ('cancelled', 'ملغي'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('monthly', 'شهري'),
        ('yearly', 'سنوي'),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('paid', 'مدفوع'),
        ('unpaid', 'غير مدفوع'),
    ]

    # بيانات العميل
    company_name = models.CharField('اسم الشركة أو المنظّم', max_length=200)
    contact_email = models.EmailField('البريد الإلكتروني')
    contact_phone = models.CharField('رقم الهاتف', max_length=30)

    # ربط اختياري بمستخدم مسجّل (لعرض الداشبورد)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                             null=True, blank=True, related_name='contracts')

    # الباقة والمدة
    package = models.ForeignKey(Package, on_delete=models.PROTECT, related_name='contracts',
                                verbose_name='الباقة المختارة')
    start_date = models.DateField('تاريخ بداية العقد', default=timezone.now)
    end_date = models.DateField('تاريخ نهاية العقد', null=True, blank=True)

    # الحالة والدفع
    status = models.CharField('حالة العقد', max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField('طريقة الدفع', max_length=10, choices=PAYMENT_METHOD_CHOICES, default='monthly')
    payment_status = models.CharField('حالة الدفع', max_length=10, choices=PAYMENT_STATUS_CHOICES, default='unpaid')

    notes = models.TextField('ملاحظات', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Contract'
        verbose_name_plural = 'Contracts'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.company_name} — {self.package}'

    @property
    def amount(self):
        """قيمة العقد حسب طريقة الدفع المختارة."""
        if self.payment_method == 'yearly':
            return self.package.price_yearly
        return self.package.price_monthly

    def save(self, *args, **kwargs):
        # احسب تاريخ النهاية تلقائيًا لو مش متحدّد
        if not self.end_date and self.start_date:
            from datetime import timedelta
            days = 365 if self.payment_method == 'yearly' else 30
            self.end_date = self.start_date + timedelta(days=days)
        super().save(*args, **kwargs)

    @property
    def is_currently_active(self):
        return self.status == 'active' and (self.end_date is None or self.end_date >= timezone.now().date())

    @property
    def days_remaining(self):
        if not self.end_date:
            return None
        return (self.end_date - timezone.now().date()).days


class Invoice(models.Model):
    """فاتورة مرتبطة بعقد."""
    STATUS_CHOICES = [
        ('paid', 'مدفوعة'),
        ('unpaid', 'غير مدفوعة'),
    ]

    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='invoices',
                                 verbose_name='العقد')
    number = models.CharField('رقم الفاتورة', max_length=30, unique=True, blank=True)
    amount = models.DecimalField('المبلغ', max_digits=10, decimal_places=2, default=0)
    issued_date = models.DateField('تاريخ الفاتورة', default=timezone.now)
    status = models.CharField('حالة الدفع', max_length=10, choices=STATUS_CHOICES, default='unpaid')
    pdf = models.FileField('ملف PDF', upload_to='invoices/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'
        ordering = ['-issued_date', '-id']

    def __str__(self):
        return self.number or f'INV-{self.pk}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # توليد رقم فاتورة بعد توفّر الـ id
        if not self.number:
            self.number = f'INV-{self.issued_date:%Y%m}-{self.pk:05d}'
            super().save(update_fields=['number'])

    def get_absolute_url(self):
        return reverse('subscriptions:invoice_detail', kwargs={'pk': self.pk})
