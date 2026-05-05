"""
Accounts Views - تسجيل الدخول، التسجيل، الملف الشخصي
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from .forms import RegisterForm, LoginForm, ProfileUpdateForm

User = get_user_model()


def register_view(request):
    """
    صفحة التسجيل - تتعامل مع GET (عرض النموذج) و POST (معالجة البيانات)
    """
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome {user.first_name}! Your account has been created.')
            return redirect('dashboard:index')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """
    صفحة تسجيل الدخول
    نستخدم email بدل username للدخول
    """
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next', 'dashboard:index')
            messages.success(request, f'Welcome back, {user.first_name}!')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid email or password.')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """تسجيل الخروج"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('accounts:login')


@login_required
def profile_view(request):
    """عرض وتحديث الملف الشخصي"""
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = ProfileUpdateForm(instance=request.user)

    context = {
        'form': form,
        'bookings': request.user.bookings.select_related('event').order_by('-booked_at')[:5],
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def user_list_view(request):
    """قائمة المستخدمين - للإدارة فقط"""
    if not request.user.is_organizer:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard:index')

    users = User.objects.all().order_by('-created_at')
    return render(request, 'accounts/user_list.html', {'users': users})
