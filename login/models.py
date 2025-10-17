from django.db import models


class User(models.Model):
    # Personal Info
    name = models.CharField(max_length=100, default="John Doe")
    email = models.EmailField(unique=True, primary_key=True)
    # Extra Info
    bio = models.TextField(blank=True)
    interests = models.TextField(blank=True)
    picture_url = models.URLField(blank=True)

    def make_post(self):
        print("Making a post placeholder!\n")

class Admin(User):
    def ban_user(self, target_user):
        print("Banning user: " + target_user + "!\n")