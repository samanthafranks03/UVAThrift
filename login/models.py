from django.db import models

class User(models.Model):
    # Personal Data
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)

    # Extra Data
    bio = models.TextField(blank=True)
    interests = models.TextField(blank=True)
    picture_url = models.URLField(blank=True)

    def make_post(self):
        print("Making a post placeholder!\n")
        return

class Admin(User):

    def ban_user(self, target_user):
        print("Banning user: " + target_user + "!\n")
        return

    pass