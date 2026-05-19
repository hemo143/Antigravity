"""
Home (Landing Page) Views
"""
import json
import logging
import threading
import urllib.request
import urllib.error
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from .models import PortfolioProject, QuoteRequest

logger = logging.getLogger(__name__)


def home_view(request):
    portfolio_items = PortfolioProject.objects.filter(is_featured=True).exclude(event_type='exhibition')
    return render(request, 'home/index.html', {'portfolio_items': portfolio_items})


def how_we_work_view(request):
    return render(request, 'home/how_we_work.html')


# ─── Resend HTTP API helpers ───────────────────────────────────────────
RESEND_ENDPOINT = 'https://api.resend.com/emails'


def _resend_send(*, from_addr: str, to: list, subject: str, html: str, text: str, reply_to: str = None) -> tuple:
    """POST a single email via Resend's HTTP API. Returns (ok, info)."""
    api_key = settings.RESEND_API_KEY
    if not api_key:
        return False, 'RESEND_API_KEY is not set'

    payload = {
        'from': from_addr,
        'to': to,
        'subject': subject,
        'html': html,
        'text': text,
    }
    if reply_to:
        payload['reply_to'] = reply_to

    req = urllib.request.Request(
        RESEND_ENDPOINT,
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'ProEvent-Site/1.0 (+https://proevent.onrender.com)',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode('utf-8'))
            return True, body.get('id', 'sent')
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode('utf-8')
        except Exception:
            err_body = ''
        return False, f'HTTP {e.code}: {err_body[:300]}'
    except Exception as e:
        return False, f'{type(e).__name__}: {e}'


def _send_quote_emails(quote: QuoteRequest) -> None:
    """Send notification to staff + acknowledgement to the client via Resend."""
    from_addr = settings.RESEND_FROM_EMAIL
    notify_to = settings.QUOTE_NOTIFICATION_EMAIL or from_addr

    if not settings.RESEND_API_KEY:
        logger.warning('Quote #%s saved but RESEND_API_KEY missing; skipping email.', quote.pk)
        return

    # ── 1) Internal notification ─────────────────────────────────────
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

    ok, info = _resend_send(
        from_addr=f'Pro Event <{from_addr}>',
        to=[notify_to],
        subject=notify_subject,
        html=notify_html,
        text=notify_text,
        reply_to=quote.email or None,
    )
    if ok:
        logger.info('Quote #%s notification sent to %s (id=%s)', quote.pk, notify_to, info)
    else:
        logger.error('Quote #%s notification FAILED: %s', quote.pk, info)

    # ── 2) Client acknowledgement ────────────────────────────────────
    # NOTE: With Resend's test domain (onboarding@resend.dev) and no
    # verified custom domain, sending to addresses other than the
    # account owner returns 403. We try it anyway and log the result.
    if not quote.email:
        return

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

    ok, info = _resend_send(
        from_addr=f'Pro Event <{from_addr}>',
        to=[quote.email],
        subject=ack_subject,
        html=ack_html,
        text=ack_text,
    )
    if ok:
        logger.info('Quote #%s ack sent to %s (id=%s)', quote.pk, quote.email, info)
    else:
        logger.warning('Quote #%s ack to %s skipped (likely needs domain verification): %s', quote.pk, quote.email, info)


def _send_quote_emails_async(quote: QuoteRequest) -> None:
    """Fire-and-forget so the form response isn't blocked by network IO."""
    t = threading.Thread(target=_send_quote_emails, args=(quote,), daemon=True)
    t.start()


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
        _send_quote_emails_async(quote)
        return JsonResponse({'success': True})
    except Exception as exc:
        logger.exception('Quote submit failed')
        return JsonResponse({'success': False, 'error': str(exc)}, status=400)
