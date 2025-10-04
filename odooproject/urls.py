from django.contrib import admin as django_admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    path("django-admin/", django_admin.site.urls),  # Django's own admin
    path("admin/", include("adminFunc.urls")),  # Your custom admin
    # path("", lambda request: redirect("adminFunc:login")),  # root → login
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
