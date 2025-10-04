# admin/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.cache import never_cache

@never_cache
def admin_login(request):
    return render(request, 'adminFunc/login.html')

@never_cache
def admin_dashboard(request):
    return render(request, 'adminFunc/adminDashboard.html')

# Login view
@never_cache
def admin_login(request):
    if request.user.is_authenticated:
        return redirect('admin:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_staff:  # Only allow staff users
                login(request, user)
                messages.success(request, 'Successfully logged in!')
                return redirect('admin:dashboard')
            else:
                messages.error(request, 'You do not have permission to access this area.')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'adminFunc/login.html')

# Dashboard view
# @login_required(login_url='/admin/login/')
@never_cache
def admin_dashboard(request):
    # Check if user is staff
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this area.')
        return redirect('admin:login')
    
    # You can add context data here
    context = {
        'user': request.user,
        'total_users': User.objects.count(),  # Example data
        # Add more context as needed
    }
    
    # return render(request, 'admin/adminDashboard.html', context)
    return render(request, 'adminFunc/adminDashboard.html')

# Logout view
@never_cache
def admin_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('admin:login')