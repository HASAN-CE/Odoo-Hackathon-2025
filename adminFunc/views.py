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


# # Logout view
# @never_cache
# def admin_logout(request):
#     logout(request)
#     messages.success(request, 'You have been logged out successfully.')
#     return redirect('admin:login')