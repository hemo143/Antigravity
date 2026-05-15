"""
Home (Landing Page) Views
"""
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import PortfolioProject, QuoteRequest


def home_view(request):
    portfolio_items = PortfolioProject.objects.filter(is_featured=True).exclude(event_type='exhibition')
    return render(request, 'home/index.html', {'portfolio_items': portfolio_items})


def how_we_work_view(request):
    return render(request, 'home/how_we_work.html')


@require_POST
def quote_submit(request):
    try:
        QuoteRequest.objects.create(
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
        return JsonResponse({'success': True})
    except Exception as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=400)
