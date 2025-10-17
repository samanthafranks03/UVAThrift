import hashlib
from django.db import models
from django.urls import reverse


class User(models.Model):
    # Personal Info
    name = models.CharField(max_length=100, default="John Doe")
    email = models.EmailField(unique=True, primary_key=True)
    hashed_email = models.CharField(max_length=10, unique=True)  # Should be a unique hash per user
    # Extra Info
    bio = models.TextField(blank=True)
    interests = models.TextField(blank=True)
    picture_url = models.URLField(blank=True)
    # Moderation
    is_flagged = models.BooleanField(default=False)
    is_new_user = models.BooleanField(default=False)

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


from django.db import models

# Create your models here.
