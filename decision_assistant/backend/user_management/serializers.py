from django.contrib.auth.models import User
from rest_framework import serializers
from .models import UserProfile, DietaryPreferences, ClothingPreferences
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, label="Confirm password")
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        # UserProfile.objects.create(user=user) # Create profile on registration
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email')

    class Meta:
        model = UserProfile
        fields = ('username', 'email', 'age', 'gender', 'body_type')

    def update(self, instance, validated_data):
        # Handle User model fields
        user_data = validated_data.pop('user', {})
        if 'email' in user_data:
            instance.user.email = user_data['email']
            instance.user.save()
        
        # Handle UserProfile fields
        instance.age = validated_data.get('age', instance.age)
        instance.gender = validated_data.get('gender', instance.gender)
        instance.body_type = validated_data.get('body_type', instance.body_type)
        instance.save()
        return instance

class DietaryPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = DietaryPreferences
        fields = ('cuisine_types', 'preferred_flavors', 'price_range', 'dietary_restrictions')

class ClothingPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClothingPreferences
        fields = ('styles', 'preferred_colors', 'preferred_brands')

# Custom TokenObtainPairSerializer to include user details in login response (optional)
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['username'] = user.username
        # ...
        return token
