"""
Management Views - Supplier & Bill CRUD Views
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.core.paginator import Paginator
from .models import Supplier, Bill
from .forms import SupplierForm, BillForm, BillFilterForm


def admin_required(view_func):
    """Decorator: only staff/admin users can access"""
    from functools import wraps

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.conf import settings
            return redirect(settings.LOGIN_URL)
        if not request.user.is_organizer:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard:index')
        return view_func(request, *args, **kwargs)
    return wrapper


# ─── SUPPLIER VIEWS ───────────────────────────────────────────────────────────

@admin_required
def supplier_list_view(request):
    """قائمة الموردين"""
    q = request.GET.get('q', '')
    service = request.GET.get('service', '')

    suppliers = Supplier.objects.annotate(
        total_billed=Sum('bills__amount'),
        unpaid_count=Count('bills', filter=Q(bills__status='unpaid'))
    )

    if q:
        suppliers = suppliers.filter(
            Q(name__icontains=q) |
            Q(contact_person__icontains=q) |
            Q(email__icontains=q)
        )
    if service:
        suppliers = suppliers.filter(service_type=service)

    paginator = Paginator(suppliers, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'suppliers': page_obj,
        'service_choices': Supplier.SERVICE_CHOICES,
        'selected_service': service,
        'q': q,
        'total_suppliers': Supplier.objects.count(),
        'active_suppliers': Supplier.objects.filter(is_active=True).count(),
    }
    return render(request, 'management/supplier_list.html', context)


@admin_required
def supplier_create_view(request):
    """إنشاء مورد جديد"""
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save()
            messages.success(request, f'Supplier "{supplier.name}" created successfully!')
            return redirect('management:supplier_list')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = SupplierForm()

    return render(request, 'management/supplier_form.html', {'form': form, 'action': 'Create'})


@admin_required
def supplier_update_view(request, pk):
    """تعديل مورد"""
    supplier = get_object_or_404(Supplier, pk=pk)

    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, 'Supplier updated successfully!')
            return redirect('management:supplier_list')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = SupplierForm(instance=supplier)

    return render(request, 'management/supplier_form.html', {
        'form': form,
        'action': 'Update',
        'supplier': supplier,
    })


@admin_required
def supplier_delete_view(request, pk):
    """حذف مورد"""
    if not request.user.is_admin:
        messages.error(request, 'Only admins can delete suppliers.')
        return redirect('management:supplier_list')

    supplier = get_object_or_404(Supplier, pk=pk)

    if request.method == 'POST':
        name = supplier.name
        supplier.delete()
        messages.success(request, f'Supplier "{name}" deleted.')
        return redirect('management:supplier_list')

    return render(request, 'management/supplier_confirm_delete.html', {'supplier': supplier})


@admin_required
def supplier_detail_view(request, pk):
    """تفاصيل مورد وفواتيره"""
    supplier = get_object_or_404(Supplier, pk=pk)
    bills = supplier.bills.select_related('event').order_by('-due_date')

    total_billed = bills.aggregate(t=Sum('amount'))['t'] or 0
    total_paid = bills.aggregate(t=Sum('paid_amount'))['t'] or 0
    remaining = total_billed - total_paid

    context = {
        'supplier': supplier,
        'bills': bills,
        'total_billed': total_billed,
        'total_paid': total_paid,
        'remaining': remaining,
    }
    return render(request, 'management/supplier_detail.html', context)


# ─── BILL VIEWS ───────────────────────────────────────────────────────────────

@admin_required
def bill_list_view(request):
    """قائمة الفواتير"""
    filter_form = BillFilterForm(request.GET)
    bills = Bill.objects.select_related('supplier', 'event').order_by('-due_date')

    if filter_form.is_valid():
        supplier = filter_form.cleaned_data.get('supplier')
        status = filter_form.cleaned_data.get('status')
        event = filter_form.cleaned_data.get('event')

        if supplier:
            bills = bills.filter(supplier=supplier)
        if status:
            bills = bills.filter(status=status)
        if event:
            bills = bills.filter(event=event)

    # Aggregated totals (on filtered queryset)
    totals = bills.aggregate(
        total_amount=Sum('amount'),
        total_paid=Sum('paid_amount'),
    )
    total_amount = totals['total_amount'] or 0
    total_paid = totals['total_paid'] or 0
    total_remaining = total_amount - total_paid

    paginator = Paginator(bills, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'bills': page_obj,
        'filter_form': filter_form,
        'total_amount': total_amount,
        'total_paid': total_paid,
        'total_remaining': total_remaining,
        'unpaid_count': Bill.objects.filter(status='unpaid').count(),
        'overdue_count': sum(1 for b in Bill.objects.filter(status__in=['unpaid', 'partial']) if b.is_overdue),
    }
    return render(request, 'management/bill_list.html', context)


@admin_required
def bill_create_view(request):
    """إنشاء فاتورة جديدة"""
    if request.method == 'POST':
        form = BillForm(request.POST, request.FILES)
        if form.is_valid():
            bill = form.save()
            messages.success(request, f'Bill "{bill.title}" created successfully!')
            return redirect('management:bill_list')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = BillForm()

    return render(request, 'management/bill_form.html', {'form': form, 'action': 'Create'})


@admin_required
def bill_update_view(request, pk):
    """تعديل فاتورة"""
    bill = get_object_or_404(Bill, pk=pk)

    if request.method == 'POST':
        form = BillForm(request.POST, request.FILES, instance=bill)
        if form.is_valid():
            form.save()
            messages.success(request, 'Bill updated successfully!')
            return redirect('management:bill_list')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = BillForm(instance=bill)

    return render(request, 'management/bill_form.html', {
        'form': form,
        'action': 'Update',
        'bill': bill,
    })


@admin_required
def bill_delete_view(request, pk):
    """حذف فاتورة"""
    if not request.user.is_admin:
        messages.error(request, 'Only admins can delete bills.')
        return redirect('management:bill_list')

    bill = get_object_or_404(Bill, pk=pk)

    if request.method == 'POST':
        title = bill.title
        bill.delete()
        messages.success(request, f'Bill "{title}" deleted.')
        return redirect('management:bill_list')

    return render(request, 'management/bill_confirm_delete.html', {'bill': bill})
