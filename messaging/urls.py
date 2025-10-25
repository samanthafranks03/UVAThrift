from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.chat, name='chat'),
    path('inbox/', views.inbox, name='inbox'),
    path('create-message/', views.create_message, name='create-message'),
    path('stream-chat-messages/', views.stream_chat_messages, name='stream-chat-messages'),
]
