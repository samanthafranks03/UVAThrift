from django.urls import path

from . import views

urlpatterns = [
    path('', views.sign_in, name='sign_in'),
    path('sign-out', views.sign_out, name='sign_out'),
    path('auth-receiver', views.auth_receiver, name='auth_receiver'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('ban-user/', views.ban_user, name='ban_user'),
    path('unban-user/', views.unban_user, name='unban_user'),
]