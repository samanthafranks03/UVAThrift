from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Messaging


class MessagingAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")

    def test_inbox_requires_login(self):
        response = self.client.get("/messaging/inbox/")
        # Should redirect to login
        self.assertEqual(response.status_code, 302)

    def test_inbox_displays_user_messages(self):
        self.client.login(username="testuser", password="testpass")
        Messaging.objects.create(author=self.user, content="Hello there!")
        response = self.client.get("/messaging/inbox/")
        self.assertContains(response, "Hello there!")

    def test_create_message_rejects_empty(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.post("/messaging/create-message/", {"content": "   "})
        self.assertEqual(response.status_code, 400)

    def test_create_message_creates_valid_message(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.post("/messaging/create-message/", {"content": "Hey!"})
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Messaging.objects.filter(content="Hey!").exists())
