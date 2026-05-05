"""
Events Forms - نماذج إدارة الأحداث
"""
from django import forms
from django.utils import timezone
from .models import Event, Category, Booking


class CategoryForm(forms.ModelForm):
    """نموذج إنشاء وتعديل الفئات"""
    class Meta:
        model = Category
        fields = ['name', 'slug', 'description', 'icon', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Category Name'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'category-slug'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'bi-calendar-event'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
        }


class EventForm(forms.ModelForm):
    """نموذج إنشاء وتعديل الأحداث"""
    start_date = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={'class': 'form-control', 'type': 'datetime-local'}
        ),
        input_formats=['%Y-%m-%dT%H:%M']
    )
    end_date = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={'class': 'form-control', 'type': 'datetime-local'}
        ),
        input_formats=['%Y-%m-%dT%H:%M']
    )

    class Meta:
        model = Event
        fields = [
            'title', 'description', 'short_description', 'cover_image',
            'category', 'start_date', 'end_date', 'venue', 'venue_address',
            'city', 'is_online', 'online_link', 'capacity', 'price',
            'is_free', 'status', 'is_featured'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Event Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'short_description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Short description (max 300 chars)'}),
            'cover_image': forms.FileInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'venue': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Venue Name'}),
            'venue_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'is_online': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'online_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://zoom.us/...'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': '0.01'}),
            'is_free': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            if end_date <= start_date:
                raise forms.ValidationError("End date must be after start date.")
            if start_date < timezone.now() and not self.instance.pk:
                raise forms.ValidationError("Start date cannot be in the past for new events.")

        return cleaned_data


class BookingForm(forms.ModelForm):
    """نموذج حجز مقعد في حدث"""
    class Meta:
        model = Booking
        fields = ['tickets', 'notes']
        widgets = {
            'tickets': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Any special requirements?'}),
        }


class EventSearchForm(forms.Form):
    """نموذج البحث والفلترة في الأحداث"""
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search events...'
        })
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label='All Categories',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    city = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'})
    )
    is_free = forms.ChoiceField(
        choices=[('', 'All'), ('true', 'Free'), ('false', 'Paid')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
