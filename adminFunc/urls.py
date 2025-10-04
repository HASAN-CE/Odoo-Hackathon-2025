from django.urls import path
from . import views

app_name = 'adminFunc'

urlpatterns = [
    path('login/', views.admin_login, name='admin_login'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    # path('logout/', views.admin_logout, name='logout'),
]
