# Profile/models.py
from django.db import models
from Login.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    gender = models.CharField(max_length=10)
    dob = models.DateField()
    height_feet = models.IntegerField()
    height_inches = models.IntegerField()
    weight = models.FloatField()
    weight_unit = models.CharField(max_length=5)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.email}"