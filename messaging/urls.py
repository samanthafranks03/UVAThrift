from django.urls import path
from . import views

app_name = "messaging"

urlpatterns = [
    path("", views.chat_list, name="chat-list"),
    path("chat/<str:username>/", views.chat_view, name="chat"),
    path("send/<str:username>/", views.send_message, name="send-message"),
    path("groups/", views.group_list, name="group-list"),
    path("group/<int:group_id>/", views.group_chat, name="group-chat"),
    path("group/<int:group_id>/send/", views.send_group_message, name="send-group-message"),
]
