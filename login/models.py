from django.db import models

class BaseUser(models.Model):
    # Personal Info
    name = models.CharField(max_length=100, default="John Doe")
    email = models.EmailField(unique=True, primary_key=True)
    # Extra Info
    bio = models.TextField(blank=True)
    interests = models.TextField(blank=True)
    picture_url = models.URLField(blank=True)

    class Meta:
        abstract = True

class User(BaseUser):
    def make_post(self):
        print("Making a post placeholder!\n")

class Admin(BaseUser):
    def ban_user(self, target_user):
        print("Banning user: " + target_user + "!\n")