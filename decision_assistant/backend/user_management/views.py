from django.contrib.auth.models import User
from .models import UserProfile, DietaryPreferences, ClothingPreferences
from .serializers import (
    UserRegistrationSerializer, 
    UserProfileSerializer, 
    DietaryPreferencesSerializer, 
    ClothingPreferencesSerializer,
    MyTokenObtainPairSerializer
)
from rest_framework import generics, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
# from rest_framework.decorators import action # Not used currently
from rest_framework_simplejwt.views import TokenObtainPairView

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Automatically create UserProfile, DietaryPreferences, and ClothingPreferences
        user_profile = UserProfile.objects.create(user=user)
        DietaryPreferences.objects.create(user_profile=user_profile)
        ClothingPreferences.objects.create(user_profile=user_profile)
        
        headers = self.get_success_headers(serializer.data)
        # Return user data (excluding password) upon successful registration
        # The serializer.data for UserRegistrationSerializer includes username & email
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class UserProfileViewSet(viewsets.ModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Users can only see/edit their own profile
        return UserProfile.objects.filter(user=self.request.user)

    def get_object(self):
        # Get or create the profile for the current user
        obj, created = UserProfile.objects.get_or_create(user=self.request.user)
        # If profile was just created, also create associated preference objects
        if created:
            DietaryPreferences.objects.get_or_create(user_profile=obj)
            ClothingPreferences.objects.get_or_create(user_profile=obj)
        return obj
    
    def list(self, request, *args, **kwargs):
        # This viewset is typically for /api/users/profile/
        # which should return a single object, not a list.
        # Re-routing GET from list to retrieve the single profile object.
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    # perform_create is not strictly needed if get_object handles creation
    # and we are mostly doing PUT (update) to this singleton resource.
    # However, if a POST is made to /api/users/profile/, this would handle it.
    def perform_create(self, serializer):
        # Ensure it's associated with the current user.
        # get_or_create in get_object should mostly handle this.
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        # Handle User model email update if present in UserProfileSerializer
        user_data = serializer.validated_data.get('user', {}) # user field is not directly on UserProfileSerializer
        # Email is handled by UserProfileSerializer directly via source='user.email'
        # Need to retrieve the user instance from profile to update email
        profile_instance = serializer.instance
        
        # Check if 'email' is part of the validated data coming for the User model
        # The UserProfileSerializer has 'email' field with source='user.email'.
        # If it's part of validated_data, DRF handles nested update if serializer is set up for it.
        # My UserProfileSerializer is not set up for writable nested 'user.email' by default.
        # Let's adjust the serializer or handle it here.
        # For simplicity, handling it here:
        if 'email' in self.request.data: # Check raw request data
            email_from_request = self.request.data['email']
            if profile_instance.user.email != email_from_request:
                profile_instance.user.email = email_from_request
                profile_instance.user.save()
        
        serializer.save()


class PreferencesViewSetBase(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_user_profile(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

    def get_queryset(self):
        # Filter by the current user's profile
        user_profile = self.get_user_profile()
        return self.queryset_class.objects.filter(user_profile=user_profile)

    def get_object(self):
        # Get or create the preference object for the current user's profile
        user_profile = self.get_user_profile()
        obj, created = self.queryset_class.objects.get_or_create(user_profile=user_profile)
        return obj

    def list(self, request, *args, **kwargs):
        # Similar to UserProfile, this should return a single object.
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_create(self, serializer):
        # Associate with the current user's profile.
        # update_or_create ensures only one preference object per user profile.
        user_profile = self.get_user_profile()
        self.queryset_class.objects.update_or_create(user_profile=user_profile, defaults=serializer.validated_data)

    def perform_update(self, serializer):
        # serializer.save() will correctly update the instance fetched by get_object()
        serializer.save()


class DietaryPreferencesViewSet(PreferencesViewSetBase):
    serializer_class = DietaryPreferencesSerializer
    queryset_class = DietaryPreferences # Used by the base class

class ClothingPreferencesViewSet(PreferencesViewSetBase):
    serializer_class = ClothingPreferencesSerializer
    queryset_class = ClothingPreferences # Used by the base class
