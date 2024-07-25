# Login/urls.py

from django.urls import path
from .views import login, profile_set

urlpatterns = [
    path('login/', login, name='login'),
    path('profile-set/', profile_set, name='profile_set'),
]
