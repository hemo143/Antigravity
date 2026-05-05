"""
Dashboard Views - إحصائيات وتقارير النظام
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
from apps.events.models import Event, Category, Booking
from apps.management.models import Supplier, Bill
from django.contrib.auth import get_user_model

User = get_user_model()


@login_required
def dashboard_view(request):
    """
    الصفحة الرئيسية للـ Dashboard
    تعرض الإحصائيات وآخر الأحداث والحجوزات
    """
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)

    # ─── إحصائيات عامة ───────────────────────────────────────────
    total_events = Event.objects.count()
    published_events = Event.objects.filter(status='published').count()
    completed_events = Event.objects.filter(status='completed').count()
    cancelled_events = Event.objects.filter(status='cancelled').count()
    upcoming_events = Event.objects.filter(status='published', start_date__gt=now).count()

    total_bookings = Booking.objects.filter(status='confirmed').count()
    total_users = User.objects.count()
    new_users_this_month = User.objects.filter(created_at__gte=thirty_days_ago).count()

    # ─── إحصائيات مخصصة للمنظم ───────────────────────────────────
    if request.user.is_organizer and not request.user.is_admin:
        my_events = Event.objects.filter(organizer=request.user)
        total_events = my_events.count()
        published_events = my_events.filter(status='published').count()
        completed_events = my_events.filter(status='completed').count()
        total_bookings = Booking.objects.filter(event__organizer=request.user, status='confirmed').count()

    # ─── آخر الأحداث ─────────────────────────────────────────────
    if request.user.is_admin:
        recent_events = Event.objects.select_related('category', 'organizer').order_by('-created_at')[:8]
    else:
        recent_events = Event.objects.filter(
            organizer=request.user
        ).select_related('category').order_by('-created_at')[:8]

    # ─── آخر الحجوزات ────────────────────────────────────────────
    if request.user.is_admin:
        recent_bookings = Booking.objects.select_related('user', 'event').order_by('-booked_at')[:10]
    else:
        recent_bookings = Booking.objects.filter(
            event__organizer=request.user
        ).select_related('user', 'event').order_by('-booked_at')[:10]

    # ─── إحصائيات الفئات ─────────────────────────────────────────
    categories_stats = Category.objects.annotate(
        events_count=Count('events'),
        bookings_count=Count('events__bookings')
    ).order_by('-events_count')[:5]

    # ─── بيانات الرسم البياني (آخر 7 أيام) ──────────────────────
    chart_labels = []
    chart_bookings = []
    chart_events = []

    for i in range(6, -1, -1):
        day = now - timedelta(days=i)
        chart_labels.append(day.strftime('%b %d'))

        bookings_count = Booking.objects.filter(
            booked_at__date=day.date(),
            status='confirmed'
        ).count()
        events_count = Event.objects.filter(
            created_at__date=day.date()
        ).count()

        chart_bookings.append(bookings_count)
        chart_events.append(events_count)

    # ─── Finance / Management Stats ──────────────────────────────
    total_suppliers = Supplier.objects.filter(is_active=True).count()
    total_bills = Bill.objects.count()
    unpaid_bills_amount = Bill.objects.filter(
        status__in=['unpaid', 'partial']
    ).aggregate(total=Sum('amount'))['total'] or 0

    context = {
        # Stats Cards
        'total_events': total_events,
        'published_events': published_events,
        'completed_events': completed_events,
        'cancelled_events': cancelled_events,
        'upcoming_events': upcoming_events,
        'total_bookings': total_bookings,
        'total_users': total_users,
        'new_users_this_month': new_users_this_month,

        # Finance
        'total_suppliers': total_suppliers,
        'total_bills': total_bills,
        'unpaid_bills_amount': unpaid_bills_amount,

        # Tables
        'recent_events': recent_events,
        'recent_bookings': recent_bookings,
        'categories_stats': categories_stats,

        # Chart Data
        'chart_labels': chart_labels,
        'chart_bookings': chart_bookings,
        'chart_events': chart_events,
    }

    return render(request, 'dashboard/dashboard.html', context)
