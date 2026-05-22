"""SEO endpoints: sitemap.xml and robots.txt — kept tiny and dependency-free."""
from django.http import HttpResponse
from django.utils import timezone


SITE_URL = 'https://proevent.onrender.com'

# (path, change-frequency, priority)
PAGES = [
    ('/',              'weekly',  '1.0'),
    ('/how-we-work/',  'monthly', '0.8'),
]

LANGUAGES = ('en', 'ar')


def sitemap(request):
    today = timezone.now().date().isoformat()
    parts = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
             'xmlns:xhtml="http://www.w3.org/1999/xhtml">']

    for path, freq, prio in PAGES:
        for lang in LANGUAGES:
            loc = f'{SITE_URL}/{lang}{path}'
            parts.append('<url>')
            parts.append(f'<loc>{loc}</loc>')
            for alt in LANGUAGES:
                alt_loc = f'{SITE_URL}/{alt}{path}'
                parts.append(
                    f'<xhtml:link rel="alternate" hreflang="{alt}" href="{alt_loc}"/>'
                )
            parts.append(
                f'<xhtml:link rel="alternate" hreflang="x-default" href="{SITE_URL}/en{path}"/>'
            )
            parts.append(f'<lastmod>{today}</lastmod>')
            parts.append(f'<changefreq>{freq}</changefreq>')
            parts.append(f'<priority>{prio}</priority>')
            parts.append('</url>')

    parts.append('</urlset>')
    return HttpResponse('\n'.join(parts), content_type='application/xml')


def robots(request):
    body = (
        'User-agent: *\n'
        'Allow: /\n'
        'Disallow: /admin/\n'
        'Disallow: /accounts/\n'
        'Disallow: /dashboard/\n'
        'Disallow: /events/\n'
        'Disallow: /management/\n'
        'Disallow: /api/\n'
        'Disallow: /quote/submit/\n'
        '\n'
        f'Sitemap: {SITE_URL}/sitemap.xml\n'
    )
    return HttpResponse(body, content_type='text/plain')
