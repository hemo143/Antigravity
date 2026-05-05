"""
Events Signals - إشارات Django لإرسال الإشعارات تلقائياً
تُنفَّذ هذه الإشارات عند حدوث أحداث معينة في قاعدة البيانات
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Booking


@receiver(post_save, sender=Booking)
def send_booking_confirmation(sender, instance, created, **kwargs):
    """
    إرسال إيميل تأكيد عند إنشاء حجز جديد
    يُفعَّل تلقائياً بعد حفظ أي Booking جديد
    """
    if created and instance.status == 'confirmed':
        subject = f'Booking Confirmed: {instance.event.title}'
        message = f"""
Dear {instance.user.get_full_name()},

Your booking has been confirmed! Here are the details:

Event: {instance.event.title}
Date: {instance.event.start_date.strftime('%B %d, %Y at %I:%M %p')}
Venue: {instance.event.venue}
Tickets: {instance.tickets}
Total Price: {'Free' if instance.event.is_free else f'${instance.total_price}'}

Thank you for booking with us!

Best regards,
Event Management Team
        """.strip()

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.user.email],
                fail_silently=True,
            )
        except Exception:
            pass


@receiver(post_save, sender=Booking)
def send_cancellation_notice(sender, instance, created, **kwargs):
    """إرسال إيميل عند إلغاء الحجز"""
    if not created and instance.status == 'cancelled':
        subject = f'Booking Cancelled: {instance.event.title}'
        message = f"""
Dear {instance.user.get_full_name()},

Your booking for "{instance.event.title}" has been cancelled.

If you have any questions, please contact us.

Best regards,
Event Management Team
        """.strip()

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.user.email],
                fail_silently=True,
            )
        except Exception:
            pass
