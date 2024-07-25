# Login/models.py

from django.db import models

class User(models.Model):
    userid = models.CharField(max_length=255, unique=True)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=255, default="No username provided")
    profile_photo = models.CharField(max_length=255, default="No profile photo")
    last_login = models.DateTimeField(auto_now=True)
    firebase_metadata = models.JSONField(default=dict)

    def __str__(self):
        return self.email
