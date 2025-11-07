from django.urls import path

from . import views
from .views import UserProfileView, EditProfileView

urlpatterns = [
    path("<slug:hashed_email>/", UserProfileView.as_view(), name="user-profile"),
    path("<slug:hashed_email>/edit", EditProfileView.as_view(), name="edit-profile"),
]
