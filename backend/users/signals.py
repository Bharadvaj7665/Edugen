# from django.contrib.auth.models import User
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from .models import UserProfile

# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     """Create a UserProfile when a new User is created."""
#     if created:
#         UserProfile.objects.create(user=instance)




# users/signals.py

from django.contrib.auth.models import User
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from .models import UserProfile

@receiver(user_logged_in)
def create_user_profile_on_login(sender, user, request, **kwargs):
    """
    Creates a UserProfile when a user logs in for the first time.
    """
    try:
        # Check if a UserProfile already exists for this user.
        user.profile
    except UserProfile.DoesNotExist:
        # If not, it means this is their first login.
        UserProfile.objects.create(user=user)

    # Ensure the user is not a staff member.
    user.is_staff = False
    user.is_superuser = False
    user.save()