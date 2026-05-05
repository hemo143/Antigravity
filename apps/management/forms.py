"""
Management Forms - Supplier & Bill forms
"""
from django import forms
from .models import Supplier, Bill
from apps.events.models import Event


class SupplierForm(forms.ModelForm):
    """نموذج إنشاء وتعديل الموردين"""

    class Meta:
        model = Supplier
        fields = [
            'name', 'service_type', 'contact_person',
            'phone', 'email', 'address', 'notes', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Supplier / Company Name'
            }),
            'service_type': forms.Select(attrs={'class': 'form-select'}),
            'contact_person': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contact person name'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+20 1XX XXX XXXX'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'supplier@example.com'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Full address'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any additional notes...'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class BillForm(forms.ModelForm):
    """نموذج إنشاء وتعديل الفواتير"""

    class Meta:
        model = Bill
        fields = [
            'title', 'supplier', 'event',
            'amount', 'paid_amount', 'status',
            'issue_date', 'due_date', 'receipt', 'notes'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Bill description / service name'
            }),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'event': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0, 'step': '0.01',
                'placeholder': '0.00'
            }),
            'paid_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0, 'step': '0.01',
                'placeholder': '0.00'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'issue_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'receipt': forms.FileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Invoice number, payment reference...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active suppliers
        self.fields['supplier'].queryset = Supplier.objects.filter(is_active=True)
        # Only show published / draft events
        self.fields['event'].queryset = Event.objects.filter(
            status__in=['published', 'draft']
        ).order_by('-start_date')
        self.fields['event'].required = False
        self.fields['event'].empty_label = '— Not linked to an event —'
        self.fields['receipt'].required = False

    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get('amount')
        paid_amount = cleaned_data.get('paid_amount')
        issue_date = cleaned_data.get('issue_date')
        due_date = cleaned_data.get('due_date')

        if amount and paid_amount and paid_amount > amount:
            raise forms.ValidationError("Paid amount cannot be greater than the total amount.")

        if issue_date and due_date and due_date < issue_date:
            raise forms.ValidationError("Due date cannot be before the issue date.")

        return cleaned_data


class BillFilterForm(forms.Form):
    """نموذج فلترة الفواتير"""
    STATUS_CHOICES = [('', 'All Status')] + list(Bill.STATUS_CHOICES)

    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.filter(is_active=True),
        required=False,
        empty_label='All Suppliers',
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    event = forms.ModelChoiceField(
        queryset=Event.objects.all().order_by('-start_date'),
        required=False,
        empty_label='All Events',
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
