# adminFunc/views.py
import requests
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.db import transaction
from .models import User, Company, ExpenseCategory

def get_currency_from_country(country_name):
    """Get currency code from country using REST Countries API"""
    try:
        response = requests.get(f'https://restcountries.com/v3.1/name/{country_name}?fullText=true')
        if response.status_code == 200:
            data = response.json()
            if data and 'currencies' in data[0]:
                currencies = data[0]['currencies']
                # Get first currency code
                currency_code = list(currencies.keys())[0]
                return currency_code
    except Exception as e:
        print(f"Error fetching currency: {e}")
    
    # Fallback currency mapping
    fallback_currencies = {
        'United States': 'USD',
        'United Kingdom': 'GBP',
        'India': 'INR',
        'Germany': 'EUR',
        'France': 'EUR',
        'Canada': 'CAD',
        'Australia': 'AUD',
        'Japan': 'JPY',
        'China': 'CNY',
        'Brazil': 'BRL',
    }
    return fallback_currencies.get(country_name, 'USD')

@never_cache
def admin_login(request):
    """Handle both login and signup"""
    if request.user.is_authenticated:
        return redirect('adminFunc:admin_dashboard')
    
    if request.method == 'POST':
        # Check if it's login or signup form
        if 'login-email' in request.POST:
            # Login form submission
            username = request.POST.get('login-email')
            password = request.POST.get('login-password')
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                return redirect('adminFunc:admin_dashboard')
            else:
                messages.error(request, "Invalid email/username or password")
        
        elif 'email' in request.POST:
            # Signup form submission
            return signup_company_admin(request)
    
    return render(request, 'adminFunc/login.html')

@transaction.atomic
def signup_company_admin(request):
    """Handle company and admin user creation"""
    try:
        # Extract form data
        full_name = request.POST.get('full-name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm-password')
        company_name = request.POST.get('company-name')
        country = request.POST.get('country')
        
        # Validation
        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect('adminFunc:admin_login')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect('adminFunc:admin_login')
        
        # Get currency for country
        currency_code = get_currency_from_country(country)
        
        # Create Company
        company = Company.objects.create(
            name=company_name,
            country=country,
            currency_code=currency_code,
            currency_symbol=currency_code
        )
        
        # Create Admin User
        first_name = full_name
        last_name = ""
        if ' ' in full_name:
            name_parts = full_name.split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ""
            
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role='ADMIN',
            company=company,
            is_staff=True,
            is_superuser=True
        )
        
        # Create default expense categories
        default_categories = [
            'Travel', 'Meals', 'Accommodation', 'Office Supplies', 
            'Entertainment', 'Transportation', 'Utilities', 'Other'
        ]
        
        for category_name in default_categories:
            ExpenseCategory.objects.create(
                name=category_name,
                company=company,
                description=f"Default {category_name} expense category"
            )
        
        # Auto-login the user
        login(request, user)
        return redirect('adminFunc:admin_dashboard')
        
    except Exception as e:
        messages.error(request, f"Error creating account: {str(e)}")
        return redirect('adminFunc:admin_login')

@never_cache
@login_required
def admin_dashboard(request):
    """Admin dashboard - basic version without data"""
    return render(request, 'adminFunc/adminDashboard.html')

@never_cache
@login_required
def admin_logout(request):
    """Logout the user"""
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('adminFunc:admin_login')