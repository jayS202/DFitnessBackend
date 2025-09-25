from rest_framework import serializers
from .models import DfitUser, Profile

class ProfileSerializer(serializers.ModelSerializer):
    firebase_uid = serializers.CharField(source="user.firebase_uid", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    class Meta:
        model = Profile
        fields = ['firebase_uid','email','phone_number', 'address', 'date_of_birth', 'gender', 'height_cm', 'weight_kg', 'goal', 'trainer_required']
        extra_kwargs = {
            "phone_number": {"required": False},
            "address": {"required": False},
            "date_of_birth": {"required": False},
            "gender": {"required": False},
            "height_cm": {"required": False},
            "weight_kg": {"required": False},
            "goal": {"required": False},
            "trainer_required": {"required": False},
        }
        
    def create(self, validated_data):
        profile = Profile.objects.create(**validated_data)
        return profile
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
        
class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(required=False)

    class Meta:
        model = DfitUser
        fields = ['firebase_uid', 'email', 'first_name', 'last_name', 'created_at', 'updated_at', 'profile']
        read_only_fields = ['created_at', 'updated_at']
        extra_kwargs = {
            "firebase_uid": {"required": True},
            "email": {"required": True},
            "first_name": {"required": True},
            "last_name": {"required": False},
        }
        
        def create(self, validated_data):
            profile_data = validated_data.pop('profile', None)
            user = DfitUser.objects.create(**validated_data)
            if profile_data:
                Profile.objects.update_or_create(user=user, defaults=profile_data)
            return user
        
        def update(self, instance, validated_data):
            validated_data.pop('firebase_uid', None)  # Prevent updating firebase_uid
            validated_data.pop('email', None)   # Prevent updating email
            profile_data = validated_data.pop('profile', None)
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            if profile_data is not None:
                Profile.objects.update_or_create(user=instance, defaults=profile_data)
            return instance