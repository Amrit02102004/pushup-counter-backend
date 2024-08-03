# spentbackend/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', include('Login.urls')),
    path('profile/', include('Profile.urls')),
]
