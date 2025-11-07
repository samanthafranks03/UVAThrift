from django.urls import path
from . import views

urlpatterns = [
    path('', views.feed, name='feed'),
    path('create/', views.create_post, name='create_post'),
    path('flag/<int:post_id>/', views.toggle_flag, name='toggle_flag'),
    # Admin URLs
    path('admin/flagged/', views.admin_flagged_posts, name='admin_flagged_posts'),
    path('admin/delete/<int:post_id>/', views.admin_delete_post, name='admin_delete_post'),
    path('admin/dismiss-flags/<int:post_id>/', views.admin_dismiss_flags, name='admin_dismiss_flags'),
]
