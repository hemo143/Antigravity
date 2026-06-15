"""
فورمات نظام التعاقد — مع validation كامل.
"""
import re
from django import forms
from .models import Contract, Package


class CompanyForm(forms.Form):
    """فورم بيانات الشركة (مستقل — للاستخدام في خطوات منفصلة لو لزم)."""
    company_name = forms.CharField(
        label='اسم الشركة أو المنظّم', max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: ProEvent Productions'})
    )
    contact_email = forms.EmailField(
        label='البريد الإلكتروني',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@company.com'})
    )
    contact_phone = forms.CharField(
        label='رقم الهاتف', max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '01XXXXXXXXX', 'dir': 'ltr'})
    )

    def clean_contact_phone(self):
        phone = self.cleaned_data['contact_phone'].strip()
        digits = re.sub(r'[\s\-\+()]', '', phone)
        if not digits.isdigit() or not (7 <= len(digits) <= 15):
            raise forms.ValidationError('رقم هاتف غير صالح — اكتب رقمًا صحيحًا (7 إلى 15 رقمًا).')
        return phone


class ContractRequestForm(forms.ModelForm):
    """فورم طلب التعاقد الكامل (بيانات الشركة + الباقة + طريقة الدفع)."""

    class Meta:
        model = Contract
        fields = ['company_name', 'contact_email', 'contact_phone', 'package', 'payment_method', 'notes']
        labels = {
            'company_name': 'اسم الشركة أو المنظّم',
            'contact_email': 'البريد الإلكتروني',
            'contact_phone': 'رقم الهاتف',
            'package': 'الباقة المختارة',
            'payment_method': 'طريقة الدفع',
            'notes': 'ملاحظات إضافية (اختياري)',
        }
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ProEvent Productions'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@company.com'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '01XXXXXXXXX', 'dir': 'ltr'}),
            'package': forms.Select(attrs={'class': 'form-select'}),
            'payment_method': forms.RadioSelect(),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # اعرض الباقات المفعّلة فقط
        self.fields['package'].queryset = Package.objects.filter(is_active=True)
        self.fields['package'].empty_label = '— اختر باقة —'
        self.fields['notes'].required = False

    def clean_contact_phone(self):
        phone = self.cleaned_data['contact_phone'].strip()
        digits = re.sub(r'[\s\-\+()]', '', phone)
        if not digits.isdigit() or not (7 <= len(digits) <= 15):
            raise forms.ValidationError('رقم هاتف غير صالح — اكتب رقمًا صحيحًا (7 إلى 15 رقمًا).')
        return phone

    def clean_company_name(self):
        name = self.cleaned_data['company_name'].strip()
        if len(name) < 2:
            raise forms.ValidationError('اكتب اسمًا صحيحًا للشركة أو المنظّم.')
        return name
