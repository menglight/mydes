from django.contrib.auth.models import User
# Use djongo.models for MongoDB specific fields if needed, but for basic fields,
# django.db.models often work fine with Djongo translating them.
# For ArrayField, Djongo provides models.JSONField which can be used for lists.
# For testing with SQLite, we will use Django's native JSONField.
from django.db import models # Standard Django models
# from djongo import models as djongo_models # Commented out to avoid issues with SQLite tests

class UserProfile(models.Model):
    # Django's User model already has username, password, email.
    # We link UserProfile to Django's User model.
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=50, null=True, blank=True)
    body_type = models.CharField(max_length=50, null=True, blank=True)

    # Standard __str__ method
    def __str__(self):
        return self.user.username

class DietaryPreferences(models.Model):
    # Ensure this links to UserProfile, not User, to keep separations clear
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='dietary_preferences')
    # Using Django's native JSONField for SQLite compatibility during tests.
    # Djongo should also be able to handle this for the MongoDB default.
    # Default to an empty list.
    cuisine_types = models.JSONField(default=list, null=True, blank=True)
    preferred_flavors = models.JSONField(default=list, null=True, blank=True)
    price_range = models.CharField(max_length=10, null=True, blank=True) # e.g., '$-$$'
    dietary_restrictions = models.JSONField(default=list, null=True, blank=True)

    def __str__(self):
        return f"{self.user_profile.user.username}'s Dietary Preferences"

class ClothingPreferences(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='clothing_preferences')
    styles = models.JSONField(default=list, null=True, blank=True)
    preferred_colors = models.JSONField(default=list, null=True, blank=True)
    preferred_brands = models.JSONField(default=list, null=True, blank=True)

    def __str__(self):
        return f"{self.user_profile.user.username}'s Clothing Preferences"
