"""
Home (Landing Page) Views
"""
import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.mail import EmailMultiAlternatives, get_connection
from django.conf import settings
from .models import PortfolioProject, QuoteRequest

logger = logging.getLogger(__name__)


def home_view(request):
    portfolio_items = PortfolioProject.objects.filter(is_featured=True).exclude(event_type='exhibition')
    return render(request, 'home/index.html', {'portfolio_items': portfolio_items})


def how_we_work_view(request):
    return render(request, 'home/how_we_work.html')


def _send_quote_emails(quote: QuoteRequest) -> None:
    """Send notification to staff + acknowledgement to the client.

    Failures are logged but do not raise — the form already saved to DB.
    """
    from_addr = settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER
    if not from_addr:
        logger.warning('Quote saved but no EMAIL_HOST_USER configured; skipping mail.')
        return

    notify_to = getattr(settings, 'QUOTE_NOTIFICATION_EMAIL', from_addr) or from_addr

    # ── 1) Internal notification ───────────────────────────────────────
    notify_subject = f'[Pro Event] New Quote Request — {quote.name} / {quote.company}'

    notify_text = (
        f'A new quote request was submitted.\n\n'
        f'Name:        {quote.name}\n'
        f'Company:     {quote.company}\n'
        f'Email:       {quote.email}\n'
        f'Phone:       {quote.phone}\n'
        f'Event Type:  {quote.event_type}\n'
        f'Attendees:   {quote.attendees or "—"}\n'
        f'Event Date:  {quote.event_date or "—"}\n'
        f'Services:    {quote.services or "—"}\n\n'
        f'Notes:\n{quote.notes or "—"}\n\n'
        f'Submitted at: {quote.created_at:%Y-%m-%d %H:%M}\n'
    )

    notify_html = f'''
    <div style="font-family:Inter,Arial,sans-serif;background:#0A0E1A;color:#E5EAF2;padding:32px;">
      <div style="max-width:560px;margin:0 auto;background:#111927;border:1px solid rgba(255,255,255,0.06);border-radius:14px;padding:28px;">
        <h2 style="color:#FF6B35;margin:0 0 18px;">New Quote Request</h2>
        <table style="width:100%;border-collapse:collapse;font-size:14px;">
          <tr><td style="padding:6px 0;color:#8892A4;">Name</td><td style="padding:6px 0;"><strong>{quote.name}</strong></td></tr>
          <tr><td style="padding:6px 0;color:#8892A4;">Company</td><td style="padding:6px 0;">{quote.company}</td></tr>
          <tr><td style="padding:6px 0;color:#8892A4;">Email</td><td style="padding:6px 0;"><a href="mailto:{quote.email}" style="color:#4F8EF7;">{quote.email}</a></td></tr>
          <tr><td style="padding:6px 0;color:#8892A4;">Phone</td><td style="padding:6px 0;"><a href="tel:{quote.phone}" style="color:#4F8EF7;">{quote.phone}</a></td></tr>
          <tr><td style="padding:6px 0;color:#8892A4;">Event Type</td><td style="padding:6px 0;">{quote.event_type}</td></tr>
          <tr><td style="padding:6px 0;color:#8892A4;">Attendees</td><td style="padding:6px 0;">{quote.attendees or '—'}</td></tr>
          <tr><td style="padding:6px 0;color:#8892A4;">Event Date</td><td style="padding:6px 0;">{quote.event_date or '—'}</td></tr>
          <tr><td style="padding:6px 0;color:#8892A4;vertical-align:top;">Services</td><td style="padding:6px 0;">{quote.services or '—'}</td></tr>
        </table>
        {f'<div style="margin-top:18px;padding:14px;background:#0A0E1A;border-radius:10px;"><strong style="color:#FF6B35;">Notes:</strong><br>{quote.notes}</div>' if quote.notes else ''}
        <p style="margin-top:22px;color:#6B7A8D;font-size:12px;">Submitted {quote.created_at:%Y-%m-%d %H:%M}</p>
      </div>
    </div>
    '''

    # ── 2) Client acknowledgement ──────────────────────────────────────
    ack_subject = 'Thank you for contacting Pro Event'
    ack_text = (
        f'Hi {quote.name},\n\n'
        f'Thank you for reaching out to Pro Event. We have received your quote request '
        f'and our team will get back to you within 24 hours.\n\n'
        f'Your request summary:\n'
        f'• Event Type: {quote.event_type}\n'
        f'• Attendees: {quote.attendees or "TBD"}\n'
        f'• Event Date: {quote.event_date or "TBD"}\n'
        f'• Services: {quote.services or "—"}\n\n'
        f'If your event is urgent, feel free to reach us directly on WhatsApp.\n\n'
        f'Best regards,\n'
        f'The Pro Event Team\n'
        f'Egypt\'s #1 Technical Event Partner\n'
    )

    ack_html = f'''
    <div style="font-family:Inter,Arial,sans-serif;background:#0A0E1A;color:#E5EAF2;padding:32px;">
      <div style="max-width:560px;margin:0 auto;background:#111927;border:1px solid rgba(255,255,255,0.06);border-radius:14px;padding:32px;">
        <div style="display:inline-block;background:linear-gradient(135deg,#FFD27A,#FF6B35);color:#2A1500;font-weight:900;font-size:18px;padding:8px 14px;border-radius:10px;margin-bottom:18px;">Pro Event</div>
        <h2 style="color:#FFFFFF;margin:0 0 14px;font-size:22px;">Thank you, {quote.name}.</h2>
        <p style="color:#B0B8C8;line-height:1.7;font-size:15px;">
          We have received your quote request and our team will get back to you <strong style="color:#FFFFFF;">within 24 hours</strong>.
        </p>
        <div style="margin:22px 0;padding:18px;background:#0A0E1A;border:1px solid rgba(255,255,255,0.05);border-radius:10px;">
          <p style="margin:0 0 8px;color:#FF6B35;font-weight:700;font-size:13px;letter-spacing:1px;">YOUR REQUEST SUMMARY</p>
          <table style="width:100%;font-size:14px;color:#E5EAF2;">
            <tr><td style="padding:4px 0;color:#8892A4;">Event Type</td><td style="padding:4px 0;text-align:right;">{quote.event_type}</td></tr>
            <tr><td style="padding:4px 0;color:#8892A4;">Attendees</td><td style="padding:4px 0;text-align:right;">{quote.attendees or 'TBD'}</td></tr>
            <tr><td style="padding:4px 0;color:#8892A4;">Event Date</td><td style="padding:4px 0;text-align:right;">{quote.event_date or 'TBD'}</td></tr>
          </table>
        </div>
        <p style="color:#B0B8C8;line-height:1.7;font-size:15px;">
          If your event is urgent, feel free to reach us directly on WhatsApp.
        </p>
        <hr style="border:none;border-top:1px solid rgba(255,255,255,0.06);margin:28px 0 18px;">
        <p style="color:#6B7A8D;font-size:12px;margin:0;">
          Pro Event — Egypt's #1 Technical Event Partner<br>
          Cairo, Egypt
        </p>
      </div>
    </div>
    '''

    try:
        with get_connection() as conn:
            notify_msg = EmailMultiAlternatives(
                notify_subject, notify_text, from_addr, [notify_to],
                reply_to=[quote.email] if quote.email else None,
                connection=conn,
            )
            notify_msg.attach_alternative(notify_html, 'text/html')
            notify_msg.send()

            if quote.email:
                ack_msg = EmailMultiAlternatives(
                    ack_subject, ack_text, from_addr, [quote.email],
                    connection=conn,
                )
                ack_msg.attach_alternative(ack_html, 'text/html')
                ack_msg.send()
    except Exception as exc:
        logger.error('Failed to send quote emails for #%s: %s', quote.pk, exc, exc_info=True)


@require_POST
def quote_submit(request):
    try:
        quote = QuoteRequest.objects.create(
            name       = request.POST.get('name', '').strip(),
            company    = request.POST.get('company', '').strip(),
            email      = request.POST.get('email', '').strip(),
            phone      = request.POST.get('phone', '').strip(),
            event_type = request.POST.get('event_type', '').strip(),
            attendees  = request.POST.get('attendees', '').strip(),
            event_date = request.POST.get('event_date') or None,
            services   = ', '.join(request.POST.getlist('services')),
            notes      = request.POST.get('notes', '').strip(),
        )
        _send_quote_emails(quote)
        return JsonResponse({'success': True})
    except Exception as exc:
        logger.exception('Quote submit failed')
        return JsonResponse({'success': False, 'error': str(exc)}, status=400)
