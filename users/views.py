from django.shortcuts import render

from django.views.generic import DetailView, UpdateView
from django.urls.base import reverse
from .models import User, UserForm


class UserProfileView(DetailView):
    model = User
    template_name = "profile.html"
    slug_field = "hashed_email"
    slug_url_kwarg = "hashed_email"


class EditProfileView(UpdateView):
    model = User
    form_class = UserForm
    template_name = "edit_profile.html"
    slug_field = "hashed_email"
    slug_url_kwarg = "hashed_email"

    def get_success_url(self):
        return reverse("user-profile", kwargs={"hashed_email": self.object.hashed_email})
