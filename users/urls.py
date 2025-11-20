from django.urls import path

from . import views
from .views import UserProfileView, EditProfileView

urlpatterns = [
    path("<slug:hashed_email>/", UserProfileView.as_view(), name="user-profile"),
    path("<slug:hashed_email>/edit", EditProfileView.as_view(), name="edit-profile"),
    path("<slug:hashed_email>/s3-presign", views.s3_presign, name="s3-presign"),
    path("<slug:hashed_email>/set-picture", views.set_profile_picture, name="set-profile-picture"),
    path("<slug:hashed_email>/picture", views.s3_serve_picture, name="user-picture"),
    path("<slug:hashed_email>/delete-post/<int:post_id>", views.delete_post, name="delete-post"),
]
