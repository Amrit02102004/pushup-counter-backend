# profile/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('profile-get/', views.get_user_profile, name='get_user_profile'),
    path('profile-set/', views.set_user_profile, name='set_user_profile'),
]
