"""
إرسال إيميلات نظام التعاقد عبر Gmail SMTP (الإعدادات في settings/.env).
بنستخدم EmailMultiAlternatives عشان نبعت نسخة HTML + نص عادي.
fail_silently=True عشان لو الإيميل وقع ما يكسرش الطلب.
"""
import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives

log = logging.getLogger(__name__)


def _send(subject, to_list, text_body, html_body=None):
    if not to_list:
        return False
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=to_list,
        )
        if html_body:
            msg.attach_alternative(html_body, 'text/html')
        msg.send(fail_silently=False)
        return True
    except Exception as e:  # noqa
        log.warning('Email send failed to %s: %s', to_list, e)
        return False


def send_contract_emails(contract):
    """يبعت إيميل تأكيد للعميل + إيميل تنبيه لصاحب الموقع."""
    pkg = contract.package
    amount = contract.amount
    method = contract.get_payment_method_display()

    # ── 1) إيميل العميل ──
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
    _send(client_subject, [contract.contact_email], client_text, client_html)

    # ── 2) إيميل التنبيه لصاحب الموقع ──
    owner_email = getattr(settings, 'CONTRACT_NOTIFICATION_EMAIL', '') or settings.EMAIL_HOST_USER
    owner_subject = f'🔔 طلب تعاقد جديد — {contract.company_name} ({pkg})'
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
    _send(owner_subject, [owner_email] if owner_email else [], owner_text)
