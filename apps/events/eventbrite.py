"""
Eventbrite API helper.

ملاحظة مهمة: Eventbrite ألغت الـ public event search سنة 2020، فالـ API
بيرجّع فعاليات المؤسسة (Organization) المرتبطة بالتوكن فقط — أي فعالياتك إنت.
الدوكيومنتيشن: https://www.eventbrite.com/platform/api
"""
import requests
from django.conf import settings

EB_BASE = 'https://www.eventbriteapi.com/v3'
TIMEOUT = 15


class EventbriteError(Exception):
    """أي مشكلة في إعداد أو استدعاء Eventbrite."""
    pass


def _get(path, params=None):
    token = settings.EVENTBRITE_TOKEN
    if not token:
        raise EventbriteError('EVENTBRITE_TOKEN غير مضبوط في متغيرات البيئة.')
    resp = requests.get(
        f'{EB_BASE}{path}',
        headers={'Authorization': f'Bearer {token}'},
        params=params or {},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def get_org_id():
    """يرجّع الـ Organization ID — من الإعدادات أو يكتشفه تلقائياً من التوكن."""
    if settings.EVENTBRITE_ORG_ID:
        return settings.EVENTBRITE_ORG_ID
    data = _get('/users/me/organizations/')
    orgs = data.get('organizations', [])
    if not orgs:
        raise EventbriteError('لا توجد أي Organization مرتبطة بهذا التوكن.')
    return orgs[0]['id']


def fetch_org_events(status='live', order_by='start_asc'):
    """
    يجيب فعاليات مؤسستك من Eventbrite ويرجّعها في شكل مبسّط جاهز للعرض.
    status: live / draft / started / ended / completed / canceled / all
    """
    org_id = get_org_id()
    data = _get(
        f'/organizations/{org_id}/events/',
        params={'status': status, 'order_by': order_by, 'expand': 'venue'},
    )
    events = []
    for e in data.get('events', []):
        logo = e.get('logo') or {}
        venue = e.get('venue') or {}
        events.append({
            'id': e.get('id'),
            'name': (e.get('name') or {}).get('text', ''),
            'summary': e.get('summary') or '',
            'url': e.get('url'),
            'start': (e.get('start') or {}).get('local'),
            'end': (e.get('end') or {}).get('local'),
            'logo': logo.get('url'),
            'venue': venue.get('name'),
            'is_free': e.get('is_free', False),
        })
    return events
