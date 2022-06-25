from http import HTTPStatus

from django.test import Client, TestCase
from posts.models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Условный юзер
        cls.user = User.objects.create_user(
            username='user',
            email='user@test.ru',
            password='test123456'
        )
        # Юзер, который создает тестовый пост
        cls.author = User.objects.create_user(
            username='author',
            email='author@test.ru',
            password='test123456'
        )
        cls.group = Group.objects.create(
            title='Некая группа',
            slug='test_slug',
            description='Некое описание',
        )
        cls.post = Post.objects.create(
            id='1',
            author=cls.author,
            text='Некий пост',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_author = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author.force_login(self.author)
        self.urls = {
            '404': '/unexisting_page/',
            'admin': '/admin/',
            'index': '/',
            'group_list': f'/group/{self.group.slug}/',
            'create': '/create/',
            'profile': f'/profile/{self.author.username}/',
            'edit': f'/posts/{self.post.id}/edit/',
            'post_detail': f'/posts/{self.post.id}/',
        }

    def test_index_and_group(self):
        """Главная и группы доступны гостю"""
        urls = (
            self.urls['index'],
            self.urls['group_list'],
        )
        for url in urls:
            with self.subTest():
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_auth(self):
        """Страница создания поста доступна авторизованному пользователю."""
        response = self.authorized_client.get(self.urls['create'])
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit(self):
        """Страница редактирования поста доступна автору."""
        response = self.authorized_author.get(self.urls['edit'])
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_url(self):
        """Переадресация для гостей"""
        urls = {
            self.urls['admin']: '/admin/login/?next=/admin/',
            self.urls['create']: '/auth/login/?next=/create/',
            self.urls['edit']: f'/auth/login/?next=/posts/{self.post.id}/edit/'
        }
        for url, redirect_url in urls.items():
            with self.subTest():
                response = self.guest_client.get(url)
                self.assertRedirects(response, redirect_url)

    def test_urls_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_urls = {
            self.urls['index']: 'posts/index.html',
            self.urls['group_list']: 'posts/group_list.html',
            self.urls['create']: 'posts/create_post.html',
            self.urls['profile']: 'posts/profile.html',
            self.urls['edit']: 'posts/create_post.html',
            self.urls['post_detail']: 'posts/post_detail.html',
            self.urls['404']: 'core/404.html'
        }
        for url, template in templates_urls.items():
            with self.subTest(url=url):
                response = self.authorized_author.get(url)
                self.assertTemplateUsed(response, template)

    def test_unexisting_page(self):
        response = self.guest_client.get(self.urls['404'])
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
