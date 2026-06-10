"""
يزرع الباقات الثلاث الافتراضية (أساسي / احترافي / VIP).
يشتغل تلقائيًا عند الـ migrate (محليًا وعلى Render).
"""
from decimal import Decimal
from django.db import migrations


PACKAGES = [
    dict(
        name='basic', slug='basic', tagline='البداية المثالية للمنظّمين الجدد',
        price_monthly=Decimal('500'), price_yearly=Decimal('4800'),
        max_events=3, max_attendees=200, commission_rate=Decimal('8.00'),
        features=['صفحة فعالية مخصّصة', 'حجز تذاكر إلكتروني', 'دعم فني بالإيميل'],
        has_slido=False, has_reports=False, is_popular=False, sort_order=1,
    ),
    dict(
        name='pro', slug='pro', tagline='الأنسب للشركات والفعاليات المتوسطة',
        price_monthly=Decimal('1500'), price_yearly=Decimal('14400'),
        max_events=15, max_attendees=1000, commission_rate=Decimal('5.00'),
        features=['كل مميزات الأساسي', 'تكامل Eventbrite', 'دعم فني أولوية', 'شعارك على الصفحات'],
        has_slido=True, has_reports=True, is_popular=True, sort_order=2,
    ),
    dict(
        name='vip', slug='vip', tagline='حلّ متكامل للمؤتمرات والفعاليات الكبرى',
        price_monthly=Decimal('4000'), price_yearly=Decimal('38400'),
        max_events=100, max_attendees=10000, commission_rate=Decimal('3.00'),
        features=['كل مميزات الاحترافي', 'مدير حساب مخصّص', 'دعم فني 24/7', 'تقارير متقدّمة وتصدير', 'فريق هندسي في الموقع'],
        has_slido=True, has_reports=True, is_popular=False, sort_order=3,
    ),
]


def seed(apps, schema_editor):
    Package = apps.get_model('subscriptions', 'Package')
    for data in PACKAGES:
        Package.objects.update_or_create(name=data['name'], defaults=data)


def unseed(apps, schema_editor):
    Package = apps.get_model('subscriptions', 'Package')
    Package.objects.filter(name__in=[p['name'] for p in PACKAGES]).delete()


class Migration(migrations.Migration):
    dependencies = [('subscriptions', '0001_initial')]
    operations = [migrations.RunPython(seed, unseed)]
