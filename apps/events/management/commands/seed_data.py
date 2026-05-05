"""
Management Command: seed_data
يملأ قاعدة البيانات ببيانات تجريبية للتطوير والعرض التوضيحي
الاستخدام: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.accounts.models import User
from apps.events.models import Category, Event, Booking


CATEGORIES = [
    {'name': 'Technology', 'slug': 'technology', 'icon': 'bi-laptop', 'color': '#4f46e5', 'description': 'Tech conferences, hackathons, and workshops'},
    {'name': 'Music', 'slug': 'music', 'icon': 'bi-music-note-beamed', 'color': '#ec4899', 'description': 'Concerts, festivals, and live performances'},
    {'name': 'Business', 'slug': 'business', 'icon': 'bi-briefcase', 'color': '#0ea5e9', 'description': 'Networking events and business summits'},
    {'name': 'Sports', 'slug': 'sports', 'icon': 'bi-trophy', 'color': '#10b981', 'description': 'Sports events and fitness workshops'},
    {'name': 'Arts', 'slug': 'arts', 'icon': 'bi-palette', 'color': '#f59e0b', 'description': 'Art exhibitions, shows, and workshops'},
    {'name': 'Education', 'slug': 'education', 'icon': 'bi-book', 'color': '#8b5cf6', 'description': 'Seminars, courses, and training sessions'},
]

EVENTS_DATA = [
    {'title': 'Django & Python Summit 2024', 'category': 'technology', 'venue': 'Grand Tech Hall', 'city': 'Cairo', 'price': 0, 'capacity': 200, 'status': 'published', 'days_from_now': 15},
    {'title': 'React & Next.js Workshop', 'category': 'technology', 'venue': 'Innovation Hub', 'city': 'Alexandria', 'price': 50, 'capacity': 50, 'status': 'published', 'days_from_now': 30},
    {'title': 'Jazz Night at The Opera', 'category': 'music', 'venue': 'Cairo Opera House', 'city': 'Cairo', 'price': 80, 'capacity': 300, 'status': 'published', 'days_from_now': 7},
    {'title': 'Startup Founders Meetup', 'category': 'business', 'venue': 'WeWork Cairo', 'city': 'Cairo', 'price': 0, 'capacity': 100, 'status': 'published', 'days_from_now': 5},
    {'title': 'Digital Marketing Masterclass', 'category': 'education', 'venue': 'AUC Conference Center', 'city': 'Cairo', 'price': 120, 'capacity': 60, 'status': 'published', 'days_from_now': 45},
    {'title': 'Annual 5K Run for Charity', 'category': 'sports', 'venue': 'Maadi Corniche', 'city': 'Cairo', 'price': 20, 'capacity': 500, 'status': 'published', 'days_from_now': 20},
    {'title': 'Modern Art Exhibition', 'category': 'arts', 'venue': 'Nile Art Gallery', 'city': 'Giza', 'price': 0, 'capacity': 150, 'status': 'published', 'days_from_now': 10},
    {'title': 'AI & Machine Learning Conference', 'category': 'technology', 'venue': 'Hilton Heliopolis', 'city': 'Cairo', 'price': 200, 'capacity': 400, 'status': 'draft', 'days_from_now': 60},
]


class Command(BaseCommand):
    help = 'Seeds the database with sample data for development'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Seeding database with sample data...'))

        # Create admin
        admin, created = User.objects.get_or_create(
            email='admin@eventpro.com',
            defaults={
                'username': 'admin',
                'first_name': 'Admin',
                'last_name': 'User',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
                'is_verified': True,
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(f'  [OK] Admin created: admin@eventpro.com / admin123')

        # Create organizer
        organizer, created = User.objects.get_or_create(
            email='organizer@eventpro.com',
            defaults={
                'username': 'organizer',
                'first_name': 'Event',
                'last_name': 'Organizer',
                'role': 'organizer',
                'is_verified': True,
            }
        )
        if created:
            organizer.set_password('org123')
            organizer.save()
            self.stdout.write(f'  [OK] Organizer created: organizer@eventpro.com / org123')

        # Create attendee
        attendee, created = User.objects.get_or_create(
            email='user@eventpro.com',
            defaults={
                'username': 'attendee',
                'first_name': 'John',
                'last_name': 'Doe',
                'role': 'attendee',
            }
        )
        if created:
            attendee.set_password('user123')
            attendee.save()
            self.stdout.write(f'  [OK] Attendee created: user@eventpro.com / user123')

        # Create categories
        categories_map = {}
        for cat_data in CATEGORIES:
            cat, _ = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            categories_map[cat.slug] = cat
        self.stdout.write(f'  [OK] {len(CATEGORIES)} categories created')

        # Create events
        events_created = 0
        for data in EVENTS_DATA:
            start = timezone.now() + timedelta(days=data['days_from_now'])
            end = start + timedelta(hours=3)

            if not Event.objects.filter(title=data['title']).exists():
                event = Event.objects.create(
                    title=data['title'],
                    description=f"Join us for {data['title']}! An incredible event featuring the best speakers and networking opportunities. Don't miss this chance to connect with industry experts.",
                    short_description=f"An exciting {data['category'].replace('-', ' ')} event you won't want to miss.",
                    category=categories_map.get(data['category']),
                    organizer=organizer,
                    start_date=start,
                    end_date=end,
                    venue=data['venue'],
                    city=data['city'],
                    price=data['price'],
                    is_free=(data['price'] == 0),
                    capacity=data['capacity'],
                    status=data['status'],
                    is_featured=(events_created % 3 == 0),
                )
                events_created += 1

                # Add a booking
                if data['status'] == 'published':
                    Booking.objects.get_or_create(
                        user=attendee,
                        event=event,
                        defaults={'status': 'confirmed', 'tickets': 1}
                    )

        self.stdout.write(f'  [OK] {events_created} events created')
        self.stdout.write(self.style.SUCCESS('\nDone! Database seeded successfully.'))
        self.stdout.write('\nLogin credentials:')
        self.stdout.write('  Admin:     admin@eventpro.com     / admin123')
        self.stdout.write('  Organizer: organizer@eventpro.com / org123')
        self.stdout.write('  User:      user@eventpro.com      / user123')
