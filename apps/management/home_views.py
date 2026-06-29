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
    return render(request, 'home/index.html', {
        'portfolio_items': portfolio_items,
        'GOOGLE_SITE_VERIFICATION': getattr(settings, 'GOOGLE_SITE_VERIFICATION', ''),
    })


def how_we_work_view(request):
    return render(request, 'home/how_we_work.html', {
        'GOOGLE_SITE_VERIFICATION': getattr(settings, 'GOOGLE_SITE_VERIFICATION', ''),
    })


def about_view(request):
    return render(request, 'about.html', {
        'GOOGLE_SITE_VERIFICATION': getattr(settings, 'GOOGLE_SITE_VERIFICATION', ''),
    })


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
            'User-Agent': 'Apex Events-Site/1.0 (+https://proevent.onrender.com)',
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
    notify_subject = f'[Apex Events] New Quote Request — {quote.name} / {quote.company}'

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

    notes_block = (
        f'<tr><td colspan="2" style="padding:0 24px 8px;">'
        f'<div style="background:#0A0E1A;border-left:3px solid #FF6B35;padding:14px 18px;border-radius:6px;">'
        f'<div style="font-size:11px;font-weight:700;letter-spacing:1.5px;color:#FF6B35;text-transform:uppercase;margin-bottom:6px;">Customer Notes</div>'
        f'<div style="color:#E5EAF2;font-size:14px;line-height:1.65;">{quote.notes}</div>'
        f'</div></td></tr>'
    ) if quote.notes else ''

    notify_html = f'''<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#0A0E1A;font-family:'Helvetica Neue',Arial,sans-serif;-webkit-text-size-adjust:100%;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#0A0E1A;padding:40px 16px;">
    <tr><td align="center">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;width:100%;">

        <!-- Brand bar -->
        <tr><td style="padding:0 0 24px;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr>
              <td style="vertical-align:middle;">
                <table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>
                  <td style="background:linear-gradient(135deg,#FFD27A,#FF6B35);color:#2A1500;font-weight:900;font-size:18px;padding:9px 13px;border-radius:10px;line-height:1;letter-spacing:-0.5px;">PE</td>
                  <td style="padding-left:12px;color:#FFFFFF;font-size:18px;font-weight:800;letter-spacing:-0.5px;">Pro<span style="color:#FF6B35;">Event</span></td>
                </tr></table>
              </td>
              <td align="right" style="vertical-align:middle;color:#6B7A8D;font-size:12px;letter-spacing:1px;text-transform:uppercase;font-weight:600;">Quote Request</td>
            </tr>
          </table>
        </td></tr>

        <!-- Hero card -->
        <tr><td style="background:linear-gradient(135deg,#111927 0%,#1A2540 100%);border:1px solid rgba(255,107,53,0.18);border-radius:18px 18px 0 0;padding:32px 28px 24px;position:relative;">
          <div style="display:inline-block;background:rgba(255,107,53,0.14);border:1px solid rgba(255,107,53,0.35);color:#FFB28A;padding:5px 12px;border-radius:999px;font-size:11px;font-weight:700;letter-spacing:1.2px;text-transform:uppercase;margin-bottom:14px;">New Lead</div>
          <h1 style="color:#FFFFFF;margin:0 0 6px;font-size:24px;font-weight:800;letter-spacing:-0.8px;line-height:1.25;">{quote.name}</h1>
          <div style="color:#B0B8C8;font-size:14px;">{quote.company} &nbsp;·&nbsp; <span style="color:#FF6B35;">{quote.event_type}</span></div>
        </td></tr>

        <!-- Body card -->
        <tr><td style="background:#111927;border:1px solid rgba(255,255,255,0.06);border-top:none;border-radius:0 0 18px 18px;padding:8px 0 24px;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">

            <!-- Contact row -->
            <tr><td style="padding:18px 24px 6px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td style="width:50%;padding:14px 14px 14px 0;">
                    <div style="font-size:10px;font-weight:700;letter-spacing:1.5px;color:#6B7A8D;text-transform:uppercase;margin-bottom:6px;">Email</div>
                    <a href="mailto:{quote.email}" style="color:#4F8EF7;font-size:14px;text-decoration:none;font-weight:600;word-break:break-all;">{quote.email}</a>
                  </td>
                  <td style="width:50%;padding:14px 0 14px 14px;border-left:1px solid rgba(255,255,255,0.05);">
                    <div style="font-size:10px;font-weight:700;letter-spacing:1.5px;color:#6B7A8D;text-transform:uppercase;margin-bottom:6px;">Phone</div>
                    <a href="tel:{quote.phone}" style="color:#4F8EF7;font-size:14px;text-decoration:none;font-weight:600;">{quote.phone}</a>
                  </td>
                </tr>
              </table>
            </td></tr>

            <!-- Divider -->
            <tr><td style="padding:6px 24px;"><div style="height:1px;background:rgba(255,255,255,0.06);"></div></td></tr>

            <!-- Event grid -->
            <tr><td style="padding:8px 24px;">
              <div style="font-size:11px;font-weight:700;letter-spacing:1.5px;color:#FF6B35;text-transform:uppercase;margin-bottom:14px;">Event Details</div>
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td style="width:33.33%;padding:6px 8px 6px 0;vertical-align:top;">
                    <div style="background:#0A0E1A;border:1px solid rgba(255,255,255,0.04);border-radius:10px;padding:14px;">
                      <div style="font-size:10px;color:#6B7A8D;text-transform:uppercase;letter-spacing:1px;font-weight:600;margin-bottom:6px;">Attendees</div>
                      <div style="color:#FFFFFF;font-size:15px;font-weight:700;">{quote.attendees or '—'}</div>
                    </div>
                  </td>
                  <td style="width:33.33%;padding:6px 4px;vertical-align:top;">
                    <div style="background:#0A0E1A;border:1px solid rgba(255,255,255,0.04);border-radius:10px;padding:14px;">
                      <div style="font-size:10px;color:#6B7A8D;text-transform:uppercase;letter-spacing:1px;font-weight:600;margin-bottom:6px;">Event Date</div>
                      <div style="color:#FFFFFF;font-size:15px;font-weight:700;">{quote.event_date or 'TBD'}</div>
                    </div>
                  </td>
                  <td style="width:33.33%;padding:6px 0 6px 8px;vertical-align:top;">
                    <div style="background:#0A0E1A;border:1px solid rgba(255,255,255,0.04);border-radius:10px;padding:14px;">
                      <div style="font-size:10px;color:#6B7A8D;text-transform:uppercase;letter-spacing:1px;font-weight:600;margin-bottom:6px;">Submitted</div>
                      <div style="color:#FFFFFF;font-size:15px;font-weight:700;">{quote.created_at:%b %d, %H:%M}</div>
                    </div>
                  </td>
                </tr>
              </table>
            </td></tr>

            <!-- Services row -->
            <tr><td style="padding:8px 24px;">
              <div style="font-size:11px;font-weight:700;letter-spacing:1.5px;color:#FF6B35;text-transform:uppercase;margin-bottom:10px;">Services Required</div>
              <div style="color:#E5EAF2;font-size:14px;line-height:1.7;">
                {' '.join(f'<span style="display:inline-block;background:rgba(255,107,53,0.10);border:1px solid rgba(255,107,53,0.25);color:#FFB28A;padding:4px 11px;border-radius:6px;font-size:12px;font-weight:600;margin:2px 4px 2px 0;">{s.strip()}</span>' for s in (quote.services or '—').split(',') if s.strip())}
              </div>
            </td></tr>

            {notes_block}

            <!-- CTA -->
            <tr><td style="padding:20px 24px 8px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
                <td align="center">
                  <a href="mailto:{quote.email}?subject=Re%3A%20Your%20Pro%20Event%20Quote%20Request"
                     style="display:inline-block;background:linear-gradient(135deg,#FF8347,#FF6B35);color:#FFFFFF;font-weight:700;font-size:14px;padding:13px 28px;border-radius:10px;text-decoration:none;letter-spacing:0.3px;box-shadow:0 8px 24px rgba(255,107,53,0.30);">
                    📧 &nbsp; Reply to {quote.name.split()[0] if quote.name else 'Customer'}
                  </a>
                </td>
              </tr></table>
            </td></tr>

          </table>
        </td></tr>

        <!-- Footer -->
        <tr><td align="center" style="padding:24px 0 0;color:#6B7A8D;font-size:11px;line-height:1.6;letter-spacing:0.3px;">
          Apex Events — Egypt's #1 Technical Event Partner<br>
          This lead came from <a href="https://proevent.onrender.com" style="color:#8892A4;text-decoration:none;">proevent.onrender.com</a>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body></html>'''

    ok, info = _resend_send(
        from_addr=f'Apex Events <{from_addr}>',
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

    ack_subject = 'Thank you for contacting Apex Events'
    ack_text = (
        f'Hi {quote.name},\n\n'
        f'Thank you for reaching out to Apex Events. We have received your quote request '
        f'and our team will get back to you within 24 hours.\n\n'
        f'Your request summary:\n'
        f'• Event Type: {quote.event_type}\n'
        f'• Attendees: {quote.attendees or "TBD"}\n'
        f'• Event Date: {quote.event_date or "TBD"}\n'
        f'• Services: {quote.services or "—"}\n\n'
        f'If your event is urgent, feel free to reach us directly on WhatsApp.\n\n'
        f'Best regards,\n'
        f'The Apex Events Team\n'
        f'Egypt\'s #1 Technical Event Partner\n'
    )

    first_name = quote.name.split()[0] if quote.name else 'there'

    ack_html = f'''<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#0A0E1A;font-family:'Helvetica Neue',Arial,sans-serif;-webkit-text-size-adjust:100%;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#0A0E1A;padding:40px 16px;">
    <tr><td align="center">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;width:100%;">

        <!-- Brand bar -->
        <tr><td align="center" style="padding:0 0 28px;">
          <table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>
            <td style="background:linear-gradient(135deg,#FFD27A,#FF6B35);color:#2A1500;font-weight:900;font-size:20px;padding:11px 15px;border-radius:11px;line-height:1;letter-spacing:-0.5px;">PE</td>
            <td style="padding-left:12px;color:#FFFFFF;font-size:20px;font-weight:800;letter-spacing:-0.5px;">Pro<span style="color:#FF6B35;">Event</span></td>
          </tr></table>
        </td></tr>

        <!-- Main card -->
        <tr><td style="background:#111927;border:1px solid rgba(255,255,255,0.06);border-radius:18px;overflow:hidden;">

          <!-- Hero header with gradient -->
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr><td style="background:linear-gradient(135deg,rgba(255,107,53,0.15) 0%,rgba(79,142,247,0.10) 100%);padding:40px 32px 32px;text-align:center;border-bottom:1px solid rgba(255,255,255,0.05);">
              <div style="font-size:42px;line-height:1;margin-bottom:16px;">✨</div>
              <h1 style="color:#FFFFFF;margin:0 0 10px;font-size:28px;font-weight:800;letter-spacing:-1px;line-height:1.2;">Thank you, {first_name}.</h1>
              <p style="color:#B0B8C8;margin:0;font-size:15px;line-height:1.6;">Your request is in our hands.</p>
            </td></tr>
          </table>

          <!-- Body -->
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr><td style="padding:32px;">

              <p style="color:#E5EAF2;font-size:16px;line-height:1.75;margin:0 0 18px;">
                We have received your quote request for Apex Events's technical services. Our senior production team is reviewing the details and will reach out to you <strong style="color:#FFFFFF;">within 24 hours</strong> with a tailored proposal.
              </p>

              <!-- Request summary -->
              <div style="margin:28px 0 24px;background:#0A0E1A;border:1px solid rgba(255,255,255,0.05);border-radius:12px;padding:22px 24px;">
                <div style="font-size:11px;font-weight:700;letter-spacing:1.5px;color:#FF6B35;text-transform:uppercase;margin-bottom:14px;">Your Request</div>
                <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                  <tr>
                    <td style="padding:8px 0;color:#8892A4;font-size:13px;width:40%;">Event Type</td>
                    <td align="right" style="padding:8px 0;color:#FFFFFF;font-size:13px;font-weight:600;">{quote.event_type}</td>
                  </tr>
                  <tr>
                    <td style="padding:8px 0;color:#8892A4;font-size:13px;border-top:1px solid rgba(255,255,255,0.04);">Expected Attendees</td>
                    <td align="right" style="padding:8px 0;color:#FFFFFF;font-size:13px;font-weight:600;border-top:1px solid rgba(255,255,255,0.04);">{quote.attendees or 'To be discussed'}</td>
                  </tr>
                  <tr>
                    <td style="padding:8px 0;color:#8892A4;font-size:13px;border-top:1px solid rgba(255,255,255,0.04);">Event Date</td>
                    <td align="right" style="padding:8px 0;color:#FFFFFF;font-size:13px;font-weight:600;border-top:1px solid rgba(255,255,255,0.04);">{quote.event_date or 'To be discussed'}</td>
                  </tr>
                  {f'<tr><td style="padding:8px 0;color:#8892A4;font-size:13px;border-top:1px solid rgba(255,255,255,0.04);vertical-align:top;">Services</td><td align="right" style="padding:8px 0;color:#FFFFFF;font-size:13px;font-weight:600;border-top:1px solid rgba(255,255,255,0.04);line-height:1.5;">{quote.services}</td></tr>' if quote.services else ''}
                </table>
              </div>

              <p style="color:#B0B8C8;font-size:14px;line-height:1.7;margin:0 0 24px;">
                If your event is time-sensitive, feel free to reach us directly on WhatsApp — our team monitors it 24/7.
              </p>

              <!-- CTAs -->
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td align="center" style="padding:6px;">
                    <a href="https://wa.me/201119333199" style="display:inline-block;background:#25D366;color:#FFFFFF;font-weight:700;font-size:14px;padding:13px 26px;border-radius:10px;text-decoration:none;letter-spacing:0.3px;">💬 &nbsp; WhatsApp Us</a>
                  </td>
                  <td align="center" style="padding:6px;">
                    <a href="https://proevent.onrender.com/en/how-we-work/" style="display:inline-block;background:transparent;color:#FFFFFF;border:1px solid rgba(255,255,255,0.20);font-weight:600;font-size:14px;padding:12px 26px;border-radius:10px;text-decoration:none;letter-spacing:0.3px;">See How We Work →</a>
                  </td>
                </tr>
              </table>

            </td></tr>
          </table>

          <!-- Signature -->
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr><td style="padding:0 32px 32px;">
              <div style="border-top:1px solid rgba(255,255,255,0.05);padding-top:22px;">
                <div style="color:#FFFFFF;font-size:14px;font-weight:700;margin-bottom:2px;">The Apex Events Team</div>
                <div style="color:#6B7A8D;font-size:12px;">Egypt's #1 Technical Event Partner</div>
              </div>
            </td></tr>
          </table>

        </td></tr>

        <!-- Footer -->
        <tr><td align="center" style="padding:24px 0 0;color:#6B7A8D;font-size:11px;line-height:1.7;letter-spacing:0.3px;">
          Apex Events &nbsp;·&nbsp; Cairo, Egypt &nbsp;·&nbsp; +20 (111) 933 3199<br>
          <a href="https://proevent.onrender.com" style="color:#8892A4;text-decoration:none;">proevent.onrender.com</a>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body></html>'''

    ok, info = _resend_send(
        from_addr=f'Apex Events <{from_addr}>',
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
