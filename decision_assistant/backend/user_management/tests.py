from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase # Use APITestCase for DRF specific features
from .models import UserProfile, DietaryPreferences, ClothingPreferences

# Note on Database for Tests:
# These tests are written assuming the Django test runner will attempt to create a
# test version of the database specified in settings.py (which is MongoDB via Djongo).
# If a MongoDB instance is not available at localhost:27017 during test execution,
# these tests will fail with a ServerSelectionTimeoutError.
# Switching to SQLite for these tests is non-trivial due to Djongo's model features
# (e.g., JSONField) not mapping directly to SQLite through Django's ORM.

class UserRegistrationLoginTests(APITestCase):
    def test_user_registration_success(self):
        url = reverse('user-register') # Ensure this URL name matches your user_management.urls
        data = {
            'username': 'testuser_reg', # Unique username for this test
            'email': 'test_reg@example.com',
            'password': 'testpassword123',
            'password2': 'testpassword123'
        }
        response = self.client.post(url, data, format='json')
        
        # Check if user, profile, and preferences are created
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(User.objects.filter(username='testuser_reg').exists())
        user = User.objects.get(username='testuser_reg')
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
        user_profile = UserProfile.objects.get(user=user)
        self.assertTrue(DietaryPreferences.objects.filter(user_profile=user_profile).exists())
        self.assertTrue(ClothingPreferences.objects.filter(user_profile=user_profile).exists())

    def test_user_registration_failure_password_mismatch(self):
        url = reverse('user-register')
        data = {
            'username': 'testuser_pwmiss',
            'email': 'test_pwmiss@example.com',
            'password': 'testpassword123',
            'password2': 'testpassword456' # Mismatch
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data) # Check if error is related to password

    def test_user_registration_failure_missing_fields(self):
        url = reverse('user-register')
        data = {'username': 'testuser_missing', 'password': 'testpassword123'} # Missing email and password2
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data) # Check for email error
        self.assertIn('password2', response.data) # Check for password2 error

    def test_user_registration_failure_duplicate_username(self):
        # Create a user first
        User.objects.create_user(username='existinguser', email='original@example.com', password='testpassword123')
        url = reverse('user-register')
        data = {
            'username': 'existinguser', # Duplicate
            'email': 'new@example.com',
            'password': 'testpassword123',
            'password2': 'testpassword123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data) # Check for username error

    def test_user_login_success(self):
        User.objects.create_user(username='testloginuser', password='testpassword123', email='login@example.com')
        url = reverse('token-obtain-pair') 
        data = {'username': 'testloginuser', 'password': 'testpassword123'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_user_login_failure_invalid_credentials(self):
        User.objects.create_user(username='testloginuser2', password='testpassword123', email='login2@example.com')
        url = reverse('token-obtain-pair')
        data = {'username': 'testloginuser2', 'password': 'wrongpassword'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserProfileAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='profileuser', password='testpassword', email='profile@example.com')
        # UserProfile, DietaryPreferences, ClothingPreferences should be created on user registration.
        # Here, we simulate that by calling the registration view or creating them manually if needed.
        # For simplicity, let's ensure they exist for the test user.
        self.user_profile, _ = UserProfile.objects.get_or_create(user=self.user)
        DietaryPreferences.objects.get_or_create(user_profile=self.user_profile)
        ClothingPreferences.objects.get_or_create(user_profile=self.user_profile)

        login_url = reverse('token-obtain-pair')
        login_data = {'username': 'profileuser', 'password': 'testpassword'}
        response = self.client.post(login_url, login_data, format='json')
        self.access_token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        self.profile_url = reverse('user-profile')

    def test_get_user_profile_success(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.user.username)
        self.assertEqual(response.data['email'], self.user.email) # Check initial email

    def test_update_user_profile_success(self):
        data = {
            'age': 30,
            'gender': 'Male',
            'body_type': 'Athletic',
            'email': 'newprofilemail@example.com' # Test email update
        }
        response = self.client.put(self.profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        
        self.user_profile.refresh_from_db()
        self.user.refresh_from_db()
        
        self.assertEqual(self.user_profile.age, 30)
        self.assertEqual(self.user_profile.gender, 'Male')
        self.assertEqual(self.user.email, 'newprofilemail@example.com')

    def test_get_user_profile_unauthorized(self):
        self.client.credentials() # Clear authentication
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PreferencesAPITestsBase(APITestCase):
    # Base class for Dietary and Clothing Preferences tests
    # Base class for Dietary and Clothing Preferences tests
    # This class itself should not be discovered as a test case if it has no 'test_*' methods
    # or if its name starts with an underscore (e.g., _PreferencesAPITestsBase).
    preferences_url_name = None
    preferences_model_class = None

    def setUp(self):
        if not self.preferences_model_class or not self.preferences_url_name:
            return 
        self.user = User.objects.create_user(username='prefuser', password='testpassword', email='pref@example.com')
        self.user_profile, _ = UserProfile.objects.get_or_create(user=self.user)
        self.prefs_object, _ = self.preferences_model_class.objects.get_or_create(user_profile=self.user_profile)

        login_url = reverse('token-obtain-pair')
        response = self.client.post(login_url, {'username': 'prefuser', 'password': 'testpassword'}, format='json')
        self.access_token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        self.url = reverse(self.preferences_url_name)

    # Helper method, not a test itself. Renamed from test_get_preferences_success
    def _run_get_preferences_test(self): 
        if not self.preferences_model_class: return  # Should not run on base
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0, "Response data should not be empty")
        return response # Return for specific checks in subclasses

    def _run_get_preferences_unauthorized_test(self):
        if not self.preferences_model_class: return # Should not run on base
        self.client.credentials() # Clear auth
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def _run_update_preferences_test(self, update_data):
        response = self.client.put(self.url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.prefs_object.refresh_from_db()
        for key, value in update_data.items():
            self.assertEqual(getattr(self.prefs_object, key), value)

    def _run_create_preferences_test(self, create_data):
        response = self.client.post(self.url, create_data, format='json')
        # CreateModelMixin's create method (called by POST) returns 201 CREATED.
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.prefs_object.refresh_from_db()
        for key, value in create_data.items():
            self.assertEqual(getattr(self.prefs_object, key), value)
    

class DietaryPreferencesAPITests(PreferencesAPITestsBase):
    preferences_url_name = 'user-dietary-preferences'
    preferences_model_class = DietaryPreferences

    # Actual test methods for DietaryPreferences
    def test_get_dietary_preferences(self):
        response = self._run_get_preferences_test() # Call helper
        if response: # Ensure helper didn't skip due to being run on base
            self.assertIn('cuisine_types', response.data) # Specific check

    def test_get_dietary_preferences_unauthorized(self):
        self._run_get_preferences_unauthorized_test() # Call helper

    def test_update_dietary_preferences(self):
        data = {
            'cuisine_types': ['Italian', 'Mexican'],
            'preferred_flavors': ['Spicy', 'Savory'],
            'price_range': '$$',
            'dietary_restrictions': ['Nuts']
        }
        self._run_update_preferences_test(data) # Call helper

    def test_create_dietary_preferences(self):
        # This effectively tests POST as an update/create mechanism
        data = {'cuisine_types': ['Indian'], 'price_range': '$'}
        self._run_create_preferences_test(data) # Call helper


class ClothingPreferencesAPITests(PreferencesAPITestsBase):
    preferences_url_name = 'user-clothing-preferences'
    preferences_model_class = ClothingPreferences

    # Actual test methods for ClothingPreferences
    def test_get_clothing_preferences(self):
        response = self._run_get_preferences_test() # Call helper
        if response: # Ensure helper didn't skip
            self.assertIn('styles', response.data) # Specific check

    def test_get_clothing_preferences_unauthorized(self):
        self._run_get_preferences_unauthorized_test() # Call helper

    def test_update_clothing_preferences(self):
        data = {
            'styles': ['Casual', 'Formal'],
            'preferred_colors': ['Blue', 'Black'],
            'preferred_brands': ['BrandX', 'BrandY']
        }
        self._run_update_preferences_test(data) # Call helper

    def test_create_clothing_preferences(self):
        data = {'styles': ['Sporty'], 'preferred_colors': ['Red']}
        self._run_create_preferences_test(data) # Call helper
