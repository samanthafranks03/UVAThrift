# REFERENCES
# Claude 4.5
# Use: Adding S3 presign and picture serving URL endpoints

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
    # Admin actions from profile
    path("<slug:hashed_email>/admin/ban-user", views.admin_ban_user_profile, name="admin-ban-user-profile"),
    path("<slug:hashed_email>/admin/unban-user", views.admin_unban_user_profile, name="admin-unban-user-profile"),
    path("<slug:hashed_email>/admin/delete-post/<int:post_id>", views.admin_delete_post_profile, name="admin-delete-post-profile"),
    path("<slug:hashed_email>/admin/dismiss-flags/<int:post_id>", views.admin_dismiss_flags_profile, name="admin-dismiss-flags-profile"),
    path("<slug:hashed_email>/admin/ban-and-delete/<int:post_id>", views.admin_ban_and_delete_profile, name="admin-ban-and-delete-profile"),
    # Admin Control Panel
    path("admin/control-panel/", views.admin_control_panel, name="admin_control_panel"),
    path("admin/ban-user/", views.admin_ban_user_panel, name="admin_ban_user_panel"),
    path("admin/unban-user/", views.admin_unban_user_panel, name="admin_unban_user_panel"),
    path("admin/delete-post/<int:post_id>/", views.admin_delete_post_panel, name="admin_delete_post_panel"),
    path("admin/dismiss-flags/<int:post_id>/", views.admin_dismiss_flags_panel, name="admin_dismiss_flags_panel"),
    path("admin/ban-and-delete/<int:post_id>/", views.admin_ban_and_delete_panel, name="admin_ban_and_delete_panel"),
    # Walkthrough
    path("complete-walkthrough/", views.complete_walkthrough, name="complete-walkthrough"),
]
