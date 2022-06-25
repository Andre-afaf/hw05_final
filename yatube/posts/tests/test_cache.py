from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post, User


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='username')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост'
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache(self):
        url = reverse('posts:index')
        response_1 = self.authorized_client.get(url)
        post_0 = response_1.context['page_obj'][0]
        post_0.delete()
        Post.objects.create(
            author=self.user,
            text='Тестовый пост 2'
        )
        response_2 = self.authorized_client.get(url)
        self.assertEqual(response_1.content, response_2.content)
        cache.clear()
        response_3 = self.authorized_client.get(url)
        self.assertNotEqual(response_1.content, response_3.content)
