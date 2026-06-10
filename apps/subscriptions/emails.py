"""
إرسال إيميلات نظام التعاقد عبر Resend HTTP API.
بنستخدم Resend (مش SMTP) عشان Render في الخطة المجانية بيمنع SMTP —
ودي نفس الطريقة اللي بيشتغل بيها فورم عروض الأسعار في الموقع.

ملاحظة: مع دومين Resend التجريبي (onboarding@resend.dev) الإرسال بيوصل
لإيميلك إنت بس. عشان إيميل التأكيد يوصل لأي عميل، لازم تـverify دومين في Resend.
"""
import json
import logging
import urllib.request
import urllib.error
from django.conf import settings

log = logging.getLogger(__name__)
RESEND_ENDPOINT = 'https://api.resend.com/emails'


def _resend_send(*, from_addr, to, subject, html, text, reply_to=None):
    """يبعت إيميل واحد عبر Resend. يرجّع (ok, info)."""
    api_key = settings.RESEND_API_KEY
    if not api_key:
        return False, 'RESEND_API_KEY غير مضبوط'

    payload = {'from': from_addr, 'to': to, 'subject': subject, 'html': html, 'text': text}
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


def send_contract_emails(contract):
    """يبعت إيميل تأكيد للعميل + إيميل تنبيه لصاحب الموقع عبر Resend."""
    if not settings.RESEND_API_KEY:
        log.warning('Contract #%s saved but RESEND_API_KEY missing; skipping email.', contract.pk)
        return

    from_addr = settings.RESEND_FROM_EMAIL
    # إيميل صاحب الموقع: تخصيص للتعاقد، ثم نفس بريد عروض الأسعار، ثم البريد الافتراضي
    owner_to = (getattr(settings, 'CONTRACT_NOTIFICATION_EMAIL', '')
                or getattr(settings, 'QUOTE_NOTIFICATION_EMAIL', '')
                or from_addr)

    pkg = contract.package
    amount = contract.amount
    method = contract.get_payment_method_display()

    # ── 1) تنبيه صاحب الموقع ──
    owner_subject = f'[ProEvent] طلب تعاقد جديد — {contract.company_name} / {pkg}'
    owner_text = (
        f'عميل جديد طلب التعاقد:\n\n'
        f'الشركة/المنظّم: {contract.company_name}\n'
        f'الإيميل: {contract.contact_email}\n'
        f'الهاتف: {contract.contact_phone}\n'
        f'الباقة: {pkg}\n'
        f'طريقة الدفع: {method}\n'
        f'القيمة: {amount} ج.م\n'
        f'الحالة: {contract.get_status_display()}\n'
        f'ملاحظات: {contract.notes or "—"}\n'
    )
    owner_html = f"""
    <div style="font-family:Tahoma,Arial;direction:rtl;text-align:right;max-width:560px;margin:auto">
      <h2 style="color:#ff6b35">🔔 طلب تعاقد جديد</h2>
      <table style="border-collapse:collapse;width:100%">
        <tr><td style="padding:8px;border:1px solid #eee">الشركة/المنظّم</td><td style="padding:8px;border:1px solid #eee"><b>{contract.company_name}</b></td></tr>
        <tr><td style="padding:8px;border:1px solid #eee">الإيميل</td><td style="padding:8px;border:1px solid #eee">{contract.contact_email}</td></tr>
        <tr><td style="padding:8px;border:1px solid #eee">الهاتف</td><td style="padding:8px;border:1px solid #eee" dir="ltr">{contract.contact_phone}</td></tr>
        <tr><td style="padding:8px;border:1px solid #eee">الباقة</td><td style="padding:8px;border:1px solid #eee"><b>{pkg}</b></td></tr>
        <tr><td style="padding:8px;border:1px solid #eee">طريقة الدفع</td><td style="padding:8px;border:1px solid #eee">{method}</td></tr>
        <tr><td style="padding:8px;border:1px solid #eee">القيمة</td><td style="padding:8px;border:1px solid #eee"><b>{amount} ج.م</b></td></tr>
      </table>
      <p style="color:#666">ملاحظات: {contract.notes or "—"}</p>
    </div>"""
    ok, info = _resend_send(from_addr=from_addr, to=[owner_to], subject=owner_subject,
                            html=owner_html, text=owner_text, reply_to=contract.contact_email)
    log.info('Contract #%s owner email -> %s (%s)', contract.pk, ok, info)

    # ── 2) تأكيد العميل ──
    client_subject = f'تأكيد استلام طلب التعاقد — باقة {pkg}'
    client_text = (
        f'مرحبًا {contract.company_name},\n\n'
        f'استلمنا طلب تعاقدك على باقة "{pkg}".\n'
        f'طريقة الدفع: {method}\n'
        f'القيمة: {amount} ج.م\n'
        f'الحالة: قيد المراجعة — هنتواصل معك قريبًا لإتمام التفعيل.\n\n'
        f'شكرًا لاختيارك ProEvent.'
    )
    client_html = f"""
    <div style="font-family:Tahoma,Arial;direction:rtl;text-align:right;max-width:560px;margin:auto">
      <h2 style="color:#ff6b35">تم استلام طلبك ✅</h2>
      <p>مرحبًا <b>{contract.company_name}</b>،</p>
      <p>استلمنا طلب تعاقدك وهو الآن <b>قيد المراجعة</b>. التفاصيل:</p>
      <table style="border-collapse:collapse;width:100%">
        <tr><td style="padding:8px;border:1px solid #eee">الباقة</td><td style="padding:8px;border:1px solid #eee"><b>{pkg}</b></td></tr>
        <tr><td style="padding:8px;border:1px solid #eee">طريقة الدفع</td><td style="padding:8px;border:1px solid #eee">{method}</td></tr>
        <tr><td style="padding:8px;border:1px solid #eee">القيمة</td><td style="padding:8px;border:1px solid #eee"><b>{amount} ج.م</b></td></tr>
      </table>
      <p style="color:#666">هنتواصل معك قريبًا لإتمام التفعيل. شكرًا لاختيارك ProEvent 🎉</p>
    </div>"""
    ok, info = _resend_send(from_addr=from_addr, to=[contract.contact_email], subject=client_subject,
                            html=client_html, text=client_text)
    log.info('Contract #%s client email -> %s (%s)', contract.pk, ok, info)
