# Pushups/urls.py

from django.urls import path
from .views import process_image

urlpatterns = [
    path('process/', process_image, name='process_image'),
]
