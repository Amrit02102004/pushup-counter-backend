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
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    gender = models.CharField(max_length=10)
    dob = models.DateField()
    height_feet = models.IntegerField()
    height_inches = models.IntegerField()
    weight = models.FloatField()
    weight_unit = models.CharField(max_length=10)

    def __str__(self):
        return self.user.email