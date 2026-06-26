"""
Events Views - عرض وإدارة الأحداث
"""
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from .models import Event, Category, Booking, WishList
from .forms import EventForm, CategoryForm, BookingForm, EventSearchForm
from .eventbrite import fetch_org_events, EventbriteError


# ─── PUBLIC VIEWS ────────────────────────────────────────────────────────────

def event_list_view(request):
    """
    صفحة قائمة الأحداث مع البحث والفلترة
    متاحة للجميع بدون تسجيل دخول
    """
    events = Event.objects.filter(status='published').select_related('category', 'organizer')
    form = EventSearchForm(request.GET)

    if form.is_valid():
        q = form.cleaned_data.get('q')
        category = form.cleaned_data.get('category')
        city = form.cleaned_data.get('city')
        is_free = form.cleaned_data.get('is_free')
        date_from = form.cleaned_data.get('date_from')

        if q:
            events = events.filter(
                Q(title__icontains=q) |
                Q(description__icontains=q) |
                Q(venue__icontains=q)
            )
        if category:
            events = events.filter(category=category)
        if city:
            events = events.filter(city__icontains=city)
        if is_free == 'true':
            events = events.filter(is_free=True)
        elif is_free == 'false':
            events = events.filter(is_free=False)
        if date_from:
            events = events.filter(start_date__date__gte=date_from)

    # Pagination - 9 أحداث لكل صفحة
    paginator = Paginator(events, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()

    context = {
        'page_obj': page_obj,
        'events': page_obj,
        'form': form,
        'categories': categories,
        'total_events': events.count(),
    }
    return render(request, 'events/event_list.html', context)


def event_detail_view(request, slug):
    """صفحة تفاصيل الحدث"""
    event = get_object_or_404(Event, slug=slug, status='published')

    # التحقق من حجز المستخدم الحالي
    user_booking = None
    if request.user.is_authenticated:
        user_booking = Booking.objects.filter(
            user=request.user, event=event
        ).first()

    # أحداث مشابهة
    related_events = Event.objects.filter(
        category=event.category,
        status='published'
    ).exclude(id=event.id)[:3]

    context = {
        'event': event,
        'user_booking': user_booking,
        'related_events': related_events,
        'booking_form': BookingForm(),
    }
    return render(request, 'events/event_detail.html', context)


# ─── EVENTBRITE + SLIDO INTEGRATION ───────────────────────────────────────────

def eventbrite_events_view(request):
    """
    يعرض فعاليات مؤسستك مباشرة من Eventbrite API.
    لو التوكن مش مضبوط أو فيه مشكلة اتصال، بنعرض رسالة بدل ما الصفحة تقع.
    """
    eb_events, error = [], None
    if not settings.EVENTBRITE_TOKEN:
        error = 'لم يتم ضبط EVENTBRITE_TOKEN بعد.'
    else:
        try:
            eb_events = fetch_org_events(status=request.GET.get('status', 'live'))
        except EventbriteError as e:
            error = str(e)
        except requests.exceptions.HTTPError as e:
            error = f'Eventbrite رفض الطلب: {e.response.status_code} (تأكد من صلاحية التوكن).'
        except Exception as e:
            error = f'تعذّر الاتصال بـ Eventbrite: {e}'

    return render(request, 'events/eventbrite_list.html', {
        'eb_events': eb_events,
        'error': error,
    })


def event_live_view(request, slug):
    """صفحة التفاعل المباشر مع الحضور عبر Slido (iframe)."""
    event = get_object_or_404(Event, slug=slug, status='published')
    return render(request, 'events/event_live.html', {'event': event})


# ─── BOOKING VIEWS ────────────────────────────────────────────────────────────

@login_required
def book_event_view(request, slug):
    """حجز مقعد في حدث"""
    event = get_object_or_404(Event, slug=slug, status='published')

    # التحقق من عدم وجود حجز مسبق
    if Booking.objects.filter(user=request.user, event=event).exists():
        messages.warning(request, 'You have already booked this event.')
        return redirect('events:event_detail', slug=slug)

    # التحقق من توافر مقاعد
    if event.is_full:
        messages.error(request, 'Sorry, this event is fully booked.')
        return redirect('events:event_detail', slug=slug)

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.event = event
            booking.status = 'confirmed'
            booking.save()
            
            # ─── Requirement 11: Email Notification ───────────────
            try:
                subject = f'Booking Confirmation: {event.title}'
                message = f'Hi {request.user.username},\n\nYour booking for "{event.title}" on {event.start_date.strftime("%B %d, %Y")} at {event.venue} is confirmed.\n\nThank you for using Apex Events!'
                email_from = settings.DEFAULT_FROM_EMAIL
                recipient_list = [request.user.email]
                send_mail(subject, message, email_from, recipient_list, fail_silently=True)
            except Exception as e:
                print(f"Mail Error: {e}")

            messages.success(request, f'Successfully booked "{event.title}"! Check your email for confirmation.')
            return redirect('events:my_bookings')
    else:
        form = BookingForm()

    return render(request, 'events/booking_form.html', {'event': event, 'form': form})


@login_required
def cancel_booking_view(request, booking_id):
    """إلغاء حجز"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    if request.method == 'POST':
        booking.status = 'cancelled'
        booking.save()
        messages.success(request, 'Booking cancelled successfully.')
        return redirect('events:my_bookings')

    return render(request, 'events/booking_cancel.html', {'booking': booking})


@login_required
def my_bookings_view(request):
    """حجوزات المستخدم الحالي"""
    bookings = Booking.objects.filter(
        user=request.user
    ).select_related('event', 'event__category').order_by('-booked_at')

    return render(request, 'events/my_bookings.html', {'bookings': bookings})


# ─── MANAGEMENT VIEWS (للمنظمين والمشرفين) ────────────────────────────────────

@login_required
def event_create_view(request):
    """إنشاء حدث جديد"""
    if not request.user.is_organizer:
        messages.error(request, 'You do not have permission to create events.')
        return redirect('events:event_list')

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user
            event.save()
            messages.success(request, f'Event "{event.title}" created successfully!')
            return redirect('events:event_detail', slug=event.slug)
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = EventForm()

    return render(request, 'events/event_form.html', {'form': form, 'action': 'Create'})


@login_required
def event_update_view(request, slug):
    """تعديل حدث موجود"""
    event = get_object_or_404(Event, slug=slug)

    # التحقق من الصلاحية
    if not (request.user == event.organizer or request.user.is_admin):
        messages.error(request, 'You do not have permission to edit this event.')
        return redirect('events:event_detail', slug=slug)

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Event updated successfully!')
            return redirect('events:event_detail', slug=event.slug)
    else:
        form = EventForm(instance=event)

    return render(request, 'events/event_form.html', {
        'form': form,
        'event': event,
        'action': 'Update'
    })


@login_required
def event_delete_view(request, slug):
    """حذف حدث"""
    event = get_object_or_404(Event, slug=slug)

    if not (request.user == event.organizer or request.user.is_admin):
        messages.error(request, 'You do not have permission to delete this event.')
        return redirect('events:event_detail', slug=slug)

    if request.method == 'POST':
        title = event.title
        event.delete()
        messages.success(request, f'Event "{title}" deleted successfully.')
        return redirect('events:event_list')

    return render(request, 'events/event_confirm_delete.html', {'event': event})


# ─── CATEGORY VIEWS ──────────────────────────────────────────────────────────

@login_required
def category_list_view(request):
    """قائمة الفئات"""
    if not request.user.is_organizer:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:index')

    categories = Category.objects.all()
    return render(request, 'events/category_list.html', {'categories': categories})


@login_required
def category_create_view(request):
    """إنشاء فئة جديدة"""
    if not request.user.is_organizer:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created successfully!')
            return redirect('events:category_list')
    else:
        form = CategoryForm()

    return render(request, 'events/category_form.html', {'form': form, 'action': 'Create'})


@login_required
def category_update_view(request, pk):
    """تعديل فئة"""
    if not request.user.is_organizer:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:index')

    category = get_object_or_404(Category, pk=pk)

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated!')
            return redirect('events:category_list')
    else:
        form = CategoryForm(instance=category)

    return render(request, 'events/category_form.html', {'form': form, 'action': 'Update', 'category': category})


@login_required
def category_delete_view(request, pk):
    """حذف فئة"""
    if not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:index')

    category = get_object_or_404(Category, pk=pk)

    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted!')
        return redirect('events:category_list')

    return render(request, 'events/category_confirm_delete.html', {'category': category})


# ─── WISHLIST VIEWS ───────────────────────────────────────────────────────────

@login_required
def toggle_wishlist_view(request, slug):
    """إضافة أو إزالة حدث من قائمة الأمنيات"""
    event = get_object_or_404(Event, slug=slug)
    wishlist_item, created = WishList.objects.get_or_create(user=request.user, event=event)

    if not created:
        wishlist_item.delete()
        messages.info(request, f'Removed "{event.title}" from your wishlist.')
    else:
        messages.success(request, f'Added "{event.title}" to your wishlist.')

    return redirect(request.META.get('HTTP_REFERER', 'events:event_detail'))


@login_required
def wishlist_list_view(request):
    """عرض قائمة أمنيات المستخدم"""
    wishlist = WishList.objects.filter(user=request.user).select_related('event', 'event__category')
    return render(request, 'events/wishlist_list.html', {'wishlist': wishlist})


# ─── ATTENDEE MANAGEMENT ──────────────────────────────────────────────────────

@login_required
def event_attendees_view(request, slug):
    """عرض قائمة الحضور لحدث معين (للمنظمين فقط)"""
    event = get_object_or_404(Event, slug=slug)
    
    if not (request.user == event.organizer or request.user.is_admin):
        messages.error(request, 'Access denied.')
        return redirect('events:event_detail', slug=slug)

    attendees = Booking.objects.filter(event=event).select_related('user').order_by('user__username')
    
    context = {
        'event': event,
        'attendees': attendees
    }
    return render(request, 'events/event_attendees.html', context)


@login_required
def mark_attendance_view(request, booking_id):
    """تحديد حضور الشخص"""
    booking = get_object_or_404(Booking, id=booking_id)
    
    if not (request.user == booking.event.organizer or request.user.is_admin):
        messages.error(request, 'Access denied.')
        return redirect('events:event_detail', slug=booking.event.slug)

    # تبديل الحالة بين confirmed و attended
    if booking.status == 'attended':
        booking.status = 'confirmed'
    else:
        booking.status = 'attended'
    
    booking.save()
    messages.success(request, f'Attendance status updated for {booking.user.get_full_name() or booking.user.username}.')
    return redirect('events:event_attendees', slug=booking.event.slug)
