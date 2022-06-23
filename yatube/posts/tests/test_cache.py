from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post, User


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.page_obj = []
        cls.user = User.objects.create_user(username='username')
        cls.page_obj.append(Post.objects.create(
            author=cls.user,
            text='Тестовый пост'
        ))

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        url = reverse('posts:index')
        posts_count = Post.objects.count()
        response = self.client.get(url)
        content = response.content
        self.assertEqual(posts_count, 1)
        Post.objects.filter(id=1).delete()
        self.assertNotEqual(posts_count, Post.objects.count())
        self.assertEqual(content, self.client.get(url).content)
        cache.clear()
        self.assertNotEqual(content, self.client.get(url).content)
