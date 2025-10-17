from django.urls import path

from . import views
from .views import UserProfileView

urlpatterns = [
    path("<slug:hashed_email>/", UserProfileView.as_view(), name="user-profile"),
]
