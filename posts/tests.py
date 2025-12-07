from django.test import TestCase
from django.utils import timezone
from django.db import IntegrityError
from users.models import User
from posts.models import Post, PostFlag

# Test creation assisted with Microsoft Copilot
class PostModelTests(TestCase):

    def setUp(self):
        self.author = User.objects.create(email="author@example.com")

    def test_post_creation_defaults(self):
        post = Post.objects.create(author=self.author, content="Hello world")
        self.assertEqual(post.title, "Unnamed Item")
        self.assertEqual(post.location, "Location not provided")
        self.assertFalse(post.is_flagged)
        self.assertIsNotNone(post.created_at)

    def test_post_str(self):
        post = Post.objects.create(author=self.author, content="x" * 60)
        self.assertEqual(str(post), f"{self.author.email}: {'x' * 30}")

    def test_post_tags_add_and_query(self):
        post = Post.objects.create(author=self.author, content="taggable")
        post.tags.add("furniture", "wood")
        post.save()
        reloaded = Post.objects.get(pk=post.pk)
        self.assertEqual(set(reloaded.tags.names()), {"furniture", "wood"})

    def test_flag_count_and_is_flagged_by_user(self):
        u1 = User.objects.create(email="u1@example.com")
        u2 = User.objects.create(email="u2@example.com")
        post = Post.objects.create(author=self.author, content="flag me")

        PostFlag.objects.create(user=u1, post=post)
        self.assertEqual(post.flag_count(), 1)
        self.assertTrue(post.is_flagged_by_user(u1))
        self.assertFalse(post.is_flagged_by_user(u2))

        PostFlag.objects.create(user=u2, post=post)
        self.assertEqual(post.flag_count(), 2)

    def test_postflag_unique_together_user_post(self):
        user = User.objects.create(email="flagger@example.com")
        post = Post.objects.create(author=self.author, content="duplicate flag test")
        PostFlag.objects.create(user=user, post=post)
        with self.assertRaises(IntegrityError):
            PostFlag.objects.create(user=user, post=post)

    def test_post_cascade_on_author_delete(self):
        post = Post.objects.create(author=self.author, content="to be deleted")
        self.assertTrue(Post.objects.filter(pk=post.pk).exists())
        self.author.delete()
        self.assertFalse(Post.objects.filter(pk=post.pk).exists())

    def test_post_flag_cascade_on_post_delete(self):
        user = User.objects.create(email="flagger@example.com")
        post = Post.objects.create(author=self.author, content="flagged post")
        flag = PostFlag.objects.create(user=user, post=post)
        self.assertTrue(PostFlag.objects.filter(pk=flag.pk).exists())
        post.delete()
        self.assertFalse(PostFlag.objects.filter(pk=flag.pk).exists())

    # Required at form level, but technically optional, so we test anyway
    def test_image_optional_on_model(self):
        post = Post.objects.create(author=self.author, content="no image post")
        self.assertIn(post.image.name, (None, ""))

    def test_title_and_location_blank_allowed(self):
        post = Post.objects.create(author=self.author, content="blank fields ok", title="", location="")
        # Either blank or default values
        self.assertIn(post.title, ["", "Unnamed Item"])
        self.assertIn(post.location, ["", "Location not provided"])

    def test_is_flagged_toggle(self):
        post = Post.objects.create(author=self.author, content="moderate me")
        self.assertFalse(post.is_flagged)
        post.is_flagged = True
        post.save()
        post.refresh_from_db()
        self.assertTrue(post.is_flagged)