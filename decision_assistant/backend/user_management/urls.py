from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserRegistrationView,
    MyTokenObtainPairView, # Renamed from UserLoginView for clarity if using JWT's default view
    UserProfileViewSet,
    DietaryPreferencesViewSet,
    ClothingPreferencesViewSet
)
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
# For UserProfile, since we are mostly dealing with the current user's profile,
# we might not need a full ModelViewSet's generated URLs like list or detail with pk.
# However, ModelViewSet is convenient. The view logic already ensures users see their own data.
# We'll register them as viewsets. The views are customized to handle single profile context.

# UserProfileViewSet will handle /api/users/profile/
# We map 'profile' to UserProfileViewSet.
# It's better to handle the single resource aspect (/profile/) in the project urls.py
# For now, this will create /profile/ and /profile/{pk}/ which is not ideal for a single user profile.
# We'll refine this in the project's urls.py or by using a RetrieveUpdateAPIView for UserProfile.
# Let's adjust UserProfileViewSet to not be registered with a router for now,
# and instead use direct path for a single resource.

router.register(r'profile-base', UserProfileViewSet, basename='userprofile-base') # Temporary for router setup, will be replaced
router.register(r'preferences/dietary-base', DietaryPreferencesViewSet, basename='dietarypreferences-base')
router.register(r'preferences/clothing-base', ClothingPreferencesViewSet, basename='clothingpreferences-base')


urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('login/', MyTokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    
    # Path for the current user's profile (GET, PUT, PATCH, DELETE)
    # UserProfileViewSet list and retrieve methods are customized to return single profile
    path('profile/', UserProfileViewSet.as_view({'get': 'list', 'put': 'update', 'patch': 'partial_update'}), name='user-profile'),
    
    # Paths for preferences, also customized to act on the current user's single preference objects
    path('preferences/dietary/', DietaryPreferencesViewSet.as_view({'get': 'list', 'post': 'create', 'put': 'update', 'patch': 'partial_update'}), name='user-dietary-preferences'),
    path('preferences/clothing/', ClothingPreferencesViewSet.as_view({'get': 'list', 'post': 'create', 'put': 'update', 'patch': 'partial_update'}), name='user-clothing-preferences'),
    
    # The router inclusion below is commented out because we are defining specific paths above
    # for more control over the URLs, especially for the singleton resources like profile.
    # path('', include(router.urls)), 
]
