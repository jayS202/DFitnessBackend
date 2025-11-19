from django.db import models

class Account(models.Model):
    firebase_uid = models.CharField(max_length=128, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.email or self.firebase_uid}"
    
class Profile(models.Model):
    user = models.OneToOneField(Account, on_delete=models.CASCADE, related_name="profile")
    phone_number = models.CharField(max_length=50, blank=True)
    role = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=32, blank=True)
    height_cm = models.FloatField(null=True, blank=True)
    weight_kg = models.FloatField(null=True, blank=True)
    goal = models.CharField(max_length=255, blank=True)
    joined_date = models.DateField(null=True, blank=True)
        
    def __str__(self):
        return f"Profile({self.user.email or self.user.firebase_uid})"
    
    