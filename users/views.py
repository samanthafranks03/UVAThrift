from django.shortcuts import render

from django.views.generic import DetailView
from .models import User

class UserProfileView(DetailView):
    model = User
    template_name = "profile.html"
    slug_field = "hashed_email"
    slug_url_kwarg = "hashed_email"
