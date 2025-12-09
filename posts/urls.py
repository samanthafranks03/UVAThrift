# REFERENCES
# Claude 4.5
# Use: Adding S3 presign and image serving URL endpoints for posts

from django.urls import path
from . import views

urlpatterns = [
    path('', views.feed, name='feed'),
    path('create/', views.create_post, name='create_post'),
    path('<slug:hashed_email>/s3-presign', views.s3_presign, name='posts-s3-presign'),
    path('<slug:hashed_email>/set-image', views.set_post_image, name='posts-set-image'),
    path('<int:post_id>/image/', views.post_image, name='post-image'),
    path('flag/<int:post_id>/', views.toggle_flag, name='toggle_flag'),
    path('status/<int:post_id>/', views.toggle_post_status, name='toggle_post_status'),
    # Admin URLs
    path('admin/flagged/', views.admin_flagged_posts, name='admin_flagged_posts'),
    path('admin/flagged-api/', views.admin_flagged_posts_api, name='admin_flagged_posts_api'),
    path('admin/delete/<int:post_id>/', views.admin_delete_post, name='admin_delete_post'),
    path('admin/dismiss-flags/<int:post_id>/', views.admin_dismiss_flags, name='admin_dismiss_flags'),
    path('admin/ban-and-delete/<int:post_id>/', views.admin_ban_and_delete, name='admin_ban_and_delete'),
]
