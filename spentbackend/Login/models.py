# Login/models.py
from django.db import models

class User(models.Model):
    userid = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=100)
    profile_photo = models.URLField(blank=True, null=True)
    firebase_metadata = models.JSONField(default=dict)
    last_login = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email
