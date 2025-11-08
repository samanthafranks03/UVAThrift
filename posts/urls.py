from django.urls import path
from . import views

urlpatterns = [
    path('', views.feed, name='feed'),
    path('create/', views.create_post, name='create_post'),
    path('<slug:hashed_email>/s3-presign', views.s3_presign, name='posts-s3-presign'),
    path('<slug:hashed_email>/set-image', views.set_post_image, name='posts-set-image'),
    path('<int:post_id>/image/', views.post_image, name='post-image'),
]
