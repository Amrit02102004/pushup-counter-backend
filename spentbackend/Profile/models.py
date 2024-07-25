# profile/models.py

from django.db import models
from Login.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')])
    dob = models.DateField()
    height_feet = models.PositiveIntegerField()
    height_inches = models.PositiveIntegerField()
    weight = models.PositiveIntegerField()
    weight_unit = models.CharField(max_length=3, choices=[('kg', 'kg'), ('lbs', 'lbs')])

    def __str__(self):
        return f"{self.user.username}'s Profile"
