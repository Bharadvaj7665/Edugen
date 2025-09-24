from django.db import models

# Create your models here.

from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    token_balance = models.DecimalField(max_digits=10, decimal_places=4, default=5.00)

    def __str__(self):
        return f"{self.user.username}'s Profile"