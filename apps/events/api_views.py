from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from .models import Event, Category, Booking
from .serializers import EventSerializer, CategorySerializer, BookingSerializer
from django.contrib.auth import get_user_model
from django.db.models import Count

User = get_user_model()

# ─── CATEGORY APIS ──────────────────────────────────────────────────────────

class CategoryListView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

# ─── EVENT APIS ─────────────────────────────────────────────────────────────

class EventListView(generics.ListCreateAPIView):
    queryset = Event.objects.filter(status='published')
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)

class EventDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'

# ─── BOOKING APIS ───────────────────────────────────────────────────────────

class BookingListView(generics.ListCreateAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Booking.objects.all()
        return Booking.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class BookingDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Booking.objects.all()
        return Booking.objects.filter(user=self.request.user)

# ─── EXTRA LOGIC & STATS ─────────────────────────────────────────────────────

class BookEventAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug):
        event = generics.get_object_or_404(Event, slug=slug, status='published')
        
        if Booking.objects.filter(user=request.user, event=event).exists():
            return Response({"error": "Already booked"}, status=status.HTTP_400_BAD_REQUEST)
        
        if event.is_full:
            return Response({"error": "Event is full"}, status=status.HTTP_400_BAD_REQUEST)
            
        serializer = BookingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, event=event, status='confirmed')
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def dashboard_stats(request):
    """
    إحصائيات سريعة للـ Dashboard عبر API
    """
    data = {
        'total_events': Event.objects.count(),
        'total_users': User.objects.count(),
        'total_bookings': Booking.objects.count(),
        'upcoming_events': Event.objects.filter(status='published').count(),
    }
    return Response(data)
