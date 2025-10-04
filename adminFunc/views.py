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

<<<<<<< HEAD
=======

# # Logout view
# @never_cache
# def admin_logout(request):
#     logout(request)
#     messages.success(request, 'You have been logged out successfully.')
#     return redirect('admin:login')
>>>>>>> e0f140f314cc50ecdc285a5ba0edcb1bf980c335
