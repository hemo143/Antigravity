"""
Views نظام الباقات والتعاقد:
- pricing_view        : صفحة الباقات
- contract_view       : فورم التعاقد (حفظ pending + إرسال إيميلات)
- client_dashboard    : داشبورد العميل (عقوده / فواتيره / فعالياته)
- invoice_detail      : عرض الفاتورة (HTML قابل للطباعة)
- invoice_pdf         : توليد PDF للفاتورة تلقائيًا (reportlab)
"""
import io
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from django.db.models import Q
from django.utils import timezone

from .models import Package, Contract, Invoice
from .forms import ContractRequestForm
from .emails import send_contract_emails


# ─── صفحة الباقات ──────────────────────────────────────────────────────────────
def pricing_view(request):
    packages = Package.objects.filter(is_active=True)
    return render(request, 'subscriptions/pricing.html', {'packages': packages})


# ─── فورم التعاقد ──────────────────────────────────────────────────────────────
def contract_view(request):
    """يعرض الفورم، ويحفظ الطلب بحالة pending + يبعت الإيميلات."""
    if request.method == 'POST':
        form = ContractRequestForm(request.POST)
        if form.is_valid():
            contract = form.save(commit=False)
            contract.status = 'pending'
            contract.payment_status = 'unpaid'
            if request.user.is_authenticated:
                contract.user = request.user
            contract.save()

            # أنشئ فاتورة أولية (غير مدفوعة) للعقد
            Invoice.objects.create(contract=contract, amount=contract.amount, status='unpaid')

            # ابعت إيميل للعميل + تنبيه لصاحب الموقع
            send_contract_emails(contract)

            messages.success(request,
                             'تم استلام طلب التعاقد بنجاح ✅ — بعتنالك إيميل تأكيد وهنتواصل معك قريبًا.')
            return redirect('subscriptions:contract_thanks')
        messages.error(request, 'فيه حقول محتاجة تتصحّح — راجع الفورم تحت.')
    else:
        # باقة مبدئية من الرابط ?package=slug
        initial = {}
        slug = request.GET.get('package')
        if slug:
            pkg = Package.objects.filter(slug=slug, is_active=True).first()
            if pkg:
                initial['package'] = pkg
        form = ContractRequestForm(initial=initial)

    return render(request, 'subscriptions/contract_form.html', {
        'form': form,
        'packages': Package.objects.filter(is_active=True),
    })


def contract_thanks_view(request):
    return render(request, 'subscriptions/contract_thanks.html')


# ─── داشبورد العميل ────────────────────────────────────────────────────────────
@login_required
def client_dashboard_view(request):
    """يعرض عقود العميل وفواتيره وفعالياته وإحصائيات سريعة."""
    user = request.user
    # العقود المرتبطة بالمستخدم أو بنفس الإيميل
    contracts = Contract.objects.filter(
        Q(user=user) | Q(contact_email__iexact=user.email)
    ).select_related('package').distinct()

    active_contract = contracts.filter(status='active').first() or contracts.first()
    invoices = Invoice.objects.filter(contract__in=contracts).select_related('contract')

    # فعاليات العميل (لو هو منظّم)
    events = getattr(user, 'organized_events', None)
    events = events.all() if events is not None else []

    context = {
        'contracts': contracts,
        'active_contract': active_contract,
        'invoices': invoices,
        'events': events,
        'stats': {
            'events_count': len(events) if hasattr(events, '__len__') else events.count(),
            'contracts_count': contracts.count(),
            'invoices_unpaid': invoices.filter(status='unpaid').count(),
            'days_remaining': active_contract.days_remaining if active_contract else None,
        },
    }
    return render(request, 'subscriptions/dashboard.html', context)


# ─── الفاتورة (HTML) ───────────────────────────────────────────────────────────
def _get_invoice_for(request, pk):
    invoice = get_object_or_404(Invoice.objects.select_related('contract', 'contract__package'), pk=pk)
    # صلاحية الوصول: الأدمن، أو صاحب العقد (بالمستخدم أو الإيميل)
    if request.user.is_authenticated and (
        request.user.is_staff
        or invoice.contract.user_id == request.user.id
        or (invoice.contract.contact_email or '').lower() == (request.user.email or '').lower()
    ):
        return invoice
    raise Http404()


@login_required
def invoice_detail_view(request, pk):
    invoice = _get_invoice_for(request, pk)
    return render(request, 'subscriptions/invoice.html', {'invoice': invoice})


# ─── توليد PDF للفاتورة (reportlab) ────────────────────────────────────────────
@login_required
def invoice_pdf_view(request, pk):
    invoice = _get_invoice_for(request, pk)
    pdf_bytes = build_invoice_pdf(invoice)
    resp = HttpResponse(pdf_bytes, content_type='application/pdf')
    resp['Content-Disposition'] = f'inline; filename="{invoice.number or invoice.pk}.pdf"'
    return resp


def build_invoice_pdf(invoice):
    """يبني فاتورة PDF احترافية بـ reportlab ويرجّعها bytes."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas

    contract = invoice.contract
    pkg = contract.package
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4
    brand = colors.HexColor('#ff6b35')
    ink = colors.HexColor('#1a1f36')
    muted = colors.HexColor('#6b7280')

    # شريط علوي
    c.setFillColor(brand)
    c.rect(0, H - 28 * mm, W, 28 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont('Helvetica-Bold', 22)
    c.drawString(20 * mm, H - 18 * mm, 'ProEvent')
    c.setFont('Helvetica', 11)
    c.drawRightString(W - 20 * mm, H - 14 * mm, 'INVOICE')
    c.drawRightString(W - 20 * mm, H - 20 * mm, invoice.number or f'INV-{invoice.pk}')

    # بيانات الفاتورة
    y = H - 45 * mm
    c.setFillColor(muted); c.setFont('Helvetica', 10)
    c.drawString(20 * mm, y, 'BILL TO')
    c.drawRightString(W - 20 * mm, y, 'DATE')
    y -= 6 * mm
    c.setFillColor(ink); c.setFont('Helvetica-Bold', 12)
    c.drawString(20 * mm, y, contract.company_name[:48])
    c.setFont('Helvetica', 11)
    c.drawRightString(W - 20 * mm, y, invoice.issued_date.strftime('%d %b %Y'))
    y -= 6 * mm
    c.setFillColor(muted); c.setFont('Helvetica', 10)
    c.drawString(20 * mm, y, contract.contact_email)
    y -= 5 * mm
    c.drawString(20 * mm, y, contract.contact_phone)

    # جدول البنود
    y -= 16 * mm
    c.setFillColor(ink); c.setFont('Helvetica-Bold', 10)
    c.setFillColor(colors.HexColor('#f1f3f8'))
    c.rect(20 * mm, y - 2 * mm, W - 40 * mm, 9 * mm, fill=1, stroke=0)
    c.setFillColor(ink)
    c.drawString(23 * mm, y, 'DESCRIPTION')
    c.drawRightString(W - 23 * mm, y, 'AMOUNT (EGP)')
    y -= 12 * mm
    c.setFont('Helvetica', 11)
    desc = f'{pkg.get_name_display()} package — {contract.get_payment_method_display()} subscription'
    c.drawString(23 * mm, y, desc[:60])
    c.drawRightString(W - 23 * mm, y, f'{invoice.amount:,.2f}')

    # الإجمالي
    y -= 14 * mm
    c.setStrokeColor(colors.HexColor('#e8ebf2')); c.line(20 * mm, y + 6 * mm, W - 20 * mm, y + 6 * mm)
    c.setFont('Helvetica-Bold', 13); c.setFillColor(ink)
    c.drawString(120 * mm, y, 'TOTAL')
    c.setFillColor(brand)
    c.drawRightString(W - 23 * mm, y, f'{invoice.amount:,.2f} EGP')

    # حالة الدفع
    y -= 12 * mm
    paid = invoice.status == 'paid'
    c.setFillColor(colors.HexColor('#1db954') if paid else colors.HexColor('#e0245e'))
    c.setFont('Helvetica-Bold', 11)
    c.drawString(20 * mm, y, 'PAID' if paid else 'UNPAID')

    # تذييل
    c.setFillColor(muted); c.setFont('Helvetica', 9)
    c.drawCentredString(W / 2, 15 * mm, 'ProEvent — Your Technical Partner for Event Success')
    c.showPage()
    c.save()
    return buf.getvalue()
