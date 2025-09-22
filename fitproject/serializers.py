from rest_framework import serializers
from .models import DfitUser, Profile

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['phone_number', 'address', 'date_of_birth', 'gender', 'height_cm', 'weight_kg', 'trainer_required']
        extra_kwargs = {
            "phone_number": {"required": False},
            "address": {"required": False},
            "date_of_birth": {"required": False},
            "gender": {"required": False},
            "height_cm": {"required": False},
            "weight_kg": {"required": False}
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
            user = DfitUser.objects.create(**validated_data)
            return user
        
        def update(self, instance, validated_data):
            validated_data.pop('firebase_uid', None)  # Prevent updating firebase_uid
            validated_data.pop('email', None)   # Prevent updating email
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            return instance