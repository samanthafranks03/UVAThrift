import hashlib
from django import forms
from django.db import models
from django.urls import reverse
from messaging.models import Notification  


class User(models.Model):
    # Personal Info
    name = models.CharField(max_length=100, default="John Doe")
    nickname = models.CharField(max_length=100, blank=True)
    email = models.EmailField(unique=True, primary_key=True)
    hashed_email = models.CharField(max_length=10, unique=True)  # Should be a unique hash per user
    # Extra Info
    bio = models.TextField(blank=True)
    interests = models.TextField(blank=True)
    picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True, default='default.jpg')
    # Moderation
    is_flagged = models.BooleanField(default=False)
    is_new_user = models.BooleanField(default=False)
    # check for admin
    is_admin = models.BooleanField(default=False)

    def make_post(self):
        print("Making a post placeholder!\n")

    def get_absolute_url(self):
        return reverse("user-profile", kwargs={"hashed_email": self.hashed_email})

    def save(self, *args, **kwargs):
        if not self.hashed_email:
            self.hashed_email = hashlib.sha256(self.email.encode()).hexdigest()[:10]
        super().save(*args, **kwargs)


class Admin(User):
    def ban_user(self, target_user):
        print("Banning user: " + target_user + "!\n")


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        # Choose fields that a user should be able to edit
        fields = [
            "name",
            "nickname",
            "bio",
            "interests",
            "picture",
        ]
        # Optional: add widgets for nicer rendering
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 4, "placeholder": "Tell us about yourself..."}),
            "interests": forms.Textarea(attrs={"rows": 3, "placeholder": "Your hobbies, passions..."}),
            "picture": forms.ClearableFileInput(),
        }