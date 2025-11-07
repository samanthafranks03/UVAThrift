from django.urls import path
from . import views

urlpatterns = [
    path('', views.feed, name='feed'),
    path('create/', views.create_post, name='create_post'),
    path('flag/<int:post_id>/', views.toggle_flag, name='toggle_flag'),
]
