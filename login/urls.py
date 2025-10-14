from django.urls import path

from . import views

urlpatterns = [
    path("", views.login, name="login"),
    path("create/", views.new_user, name="new_user"),
]