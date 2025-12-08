# REFERENCES
# Claude 4.5
# Use: Creating tests for delete account functionality

from django.test import TestCase, Client
from django.urls import reverse
from users.models import User
from posts.models import Post


class DeleteAccountTestCase(TestCase):
    """Tests for the delete account feature"""

    def setUp(self):
        """Set up test user and client"""
        self.client = Client()
        self.user = User.objects.create(
            email='testuser@example.com',
            name='Test User',
            hashed_email='testhash01'
        )

    def test_delete_account_requires_authentication(self):
        """Test that delete account requires user to be logged in"""
        response = self.client.post(
            reverse('delete-account', kwargs={'hashed_email': self.user.hashed_email})
        )
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        # User should still exist
        self.assertTrue(User.objects.filter(email='testuser@example.com').exists())

    def test_delete_account_success(self):
        """Test successful account deletion"""
        # Simulate logged in user by setting session
        session = self.client.session
        session['user_data'] = {
            'email': 'testuser@example.com',
            'name': 'Test User'
        }
        session.save()

        # Create a post by the user to test cascade deletion
        Post.objects.create(
            author=self.user,
            content='Test post content',
            title='Test Post'
        )

        # Delete account
        response = self.client.post(
            reverse('delete-account', kwargs={'hashed_email': self.user.hashed_email})
        )

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

        # User should be deleted
        self.assertFalse(User.objects.filter(email='testuser@example.com').exists())

        # User's posts should also be deleted (cascade)
        self.assertEqual(Post.objects.filter(author__email='testuser@example.com').count(), 0)

        # Session should be cleared
        self.assertNotIn('user_data', self.client.session)

    def test_delete_account_only_own_account(self):
        """Test that users can only delete their own account"""
        # Create another user
        other_user = User.objects.create(
            email='otheruser@example.com',
            name='Other User',
            hashed_email='otherhash1'
        )

        # Simulate logged in as testuser
        session = self.client.session
        session['user_data'] = {
            'email': 'testuser@example.com',
            'name': 'Test User'
        }
        session.save()

        # Try to delete other user's account
        response = self.client.post(
            reverse('delete-account', kwargs={'hashed_email': other_user.hashed_email})
        )

        # Should redirect to market (not allowed)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/market/', response.url)

        # Other user should still exist
        self.assertTrue(User.objects.filter(email='otheruser@example.com').exists())

    def test_delete_account_nonexistent_user(self):
        """Test deleting a nonexistent user account"""
        # Simulate logged in user
        session = self.client.session
        session['user_data'] = {
            'email': 'testuser@example.com',
            'name': 'Test User'
        }
        session.save()

        # Try to delete nonexistent account
        response = self.client.post(
            reverse('delete-account', kwargs={'hashed_email': 'nonexistent'})
        )

        # Should redirect to market
        self.assertEqual(response.status_code, 302)
        self.assertIn('/market/', response.url)

