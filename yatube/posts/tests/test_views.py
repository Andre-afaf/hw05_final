import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        cls.post = Post.objects.create(
            id='1',
            author=cls.author,
            text='Некий пост',
            group=cls.group,
            image=uploaded,
        )

        cls.reverse_urls = {
            'index': reverse('posts:index'),
            'group_list': reverse('posts:group_posts',
                                  kwargs={'slug': cls.group.slug}),
            'create': reverse('posts:post_create'),
            'profile': reverse('posts:profile',
                               kwargs={'username': cls.author.username}),
            'edit': reverse('posts:post_edit',
                            kwargs={'post_id': cls.post.pk}),
            'post_detail': reverse('posts:post_detail',
                                   kwargs={'post_id': cls.post.pk})
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)
        self.follower = User.objects.create_user(
            username='follower'
        )
        self.authorized_follower = Client()
        self.authorized_follower.force_login(self.follower)
        self.unfollower = User.objects.create_user(
            username='unfollower'
        )
        self.authorized_unfollower = Client()
        self.authorized_unfollower.force_login(self.unfollower)

        Follow.objects.create(user=self.author, author=self.follower)

    def test_views_use_correct_template(self):
        views_temps = {
            self.reverse_urls['index']: 'posts/index.html',
            self.reverse_urls['group_list']: 'posts/group_list.html',
            self.reverse_urls['profile']: 'posts/profile.html',
            self.reverse_urls['post_detail']: 'posts/post_detail.html',
            self.reverse_urls['edit']: 'posts/create_post.html',
            self.reverse_urls['create']: 'posts/create_post.html',
        }
        for reverse_name, template in views_temps.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_paginator_15_posts(self):
        reverse_namelist = (
            self.reverse_urls['index'],
            self.reverse_urls['group_list'],
            self.reverse_urls['profile']

        )
        for i in range(2, 17):
            Post.objects.create(
                id=i,
                author=self.author,
                text=f'Некий пост #{i}',
                group=self.group,
            )
        for n in reverse_namelist:
            response_page1 = self.client.get(n)
            response_page2 = self.client.get(n + '?page=2')
            self.assertEqual(len(response_page1.context['page_obj']), 10)
            self.assertEqual(len(response_page2.context['page_obj']), 6)

    def test_post_exist(self):
        # Самый новый пост присутствует на страницах и имеет последний индекс
        reverse_namelist = (
            self.reverse_urls['index'],
            self.reverse_urls['group_list'],
            self.reverse_urls['profile']

        )
        for i in reverse_namelist:
            response = self.authorized_author.get(i)
            self.assertEqual(response.context['page_obj'][0].id,
                             int(self.post.id))
            self.assertEqual(response.context['page_obj'][0].group, self.group)

    def test_index_context(self):
        response = self.authorized_author.get(self.reverse_urls['index'])
        first_test_object = response.context['page_obj'][0]
        post_author_0 = first_test_object.author.username
        post_text_0 = first_test_object.text
        post_group_0 = first_test_object.group.title
        post_image_0 = first_test_object.image
        self.assertEqual(post_author_0, self.author.username)
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_group_0, self.group.title)
        self.assertEqual(post_image_0, self.post.image)

    def test_group_posts_context(self):
        response = self.authorized_author.get(self.reverse_urls['group_list'])
        first_test_object = response.context['page_obj'][0]
        post_author_0 = first_test_object.author.username
        post_text_0 = first_test_object.text
        post_group_0 = first_test_object.group.title
        post_image_0 = first_test_object.image
        self.assertEqual(post_author_0, self.author.username)
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_group_0, self.group.title)
        self.assertEqual(response.context['group'], self.group)
        self.assertEqual(post_image_0, self.post.image)

    def test_profile_page_show_correct_context(self):
        response = self.authorized_author.get(self.reverse_urls['profile'])
        first_test_object = response.context['page_obj'][0]
        post_author_0 = first_test_object.author.username
        post_text_0 = first_test_object.text
        post_group_0 = first_test_object.group.title
        test_author = response.context['author']
        test_posts_count = response.context['posts_count']
        post_image_0 = first_test_object.image
        self.assertEqual(post_author_0, self.author.username)
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_group_0, self.group.title)
        self.assertEqual(test_author, self.author)
        self.assertEqual(test_posts_count, self.author.posts.count())
        self.assertEqual(post_image_0, self.post.image)

    def test_post_detail_context(self):
        response = self.authorized_author.get(self.reverse_urls['post_detail'])
        test_title = response.context['title']
        test_full_post = response.context['post']
        test_posts_count = response.context['posts_count']
        post_image_0 = response.context['image']
        post = Post.objects.get(pk=self.post.id)
        self.assertEqual(test_title, f'Пост {post.text[:30]}')
        self.assertEqual(test_full_post, post)
        self.assertEqual(test_posts_count, self.author.posts.count())
        self.assertEqual(post_image_0, self.post.image)

    def test_post_create_context(self):
        response = self.authorized_author.get(self.reverse_urls['create'])
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.MultipleChoiceField,
        }
        for value in form_fields.keys():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get('text')
                self.assertIsInstance(form_field, form_fields['text'])

    def test_post_edit_context(self):
        response = self.authorized_author.get(self.reverse_urls['edit'])
        form_fields = {'text': forms.fields.CharField}
        test_is_edit = response.context['is_edit']
        for value in form_fields.keys():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get('text')
                self.assertIsInstance(form_field, form_fields['text'])
        self.assertTrue(test_is_edit)

    def test_post_in_2_group(self):
        # Создаем тестовый пост в группе №2
        # и проверяем индексы последних постов в обеих группах

        group_2 = Group.objects.create(
            slug='Test_slug_2',
            title='Тестовая группа 2',
            description='Тестовое описание2',
        )

        Post.objects.create(
            author=self.author,
            text='Пост №2',
            group=group_2
        )
        # Смотрим, что новый пост не отображается в первой группе
        response = self.authorized_author.get(self.reverse_urls['group_list'])
        self.assertEqual(response.context['page_obj'][0].id, int(self.post.id))
        # Смотрим, что новый пост отображается на первом месте в новой группе
        response_group2 = self.authorized_author.get(
            reverse('posts:group_posts', kwargs={'slug': group_2.slug})
        )
        self.assertEqual(response_group2.context['page_obj'][0].id, 2)

    def test_following(self):
        """Тест подписки на автора."""
        client = self.authorized_author
        user = self.unfollower
        author = self.author
        follower = Follow.objects.filter(
            user=author,
            author=self.unfollower
        )
        count_1 = follower.count()
        client.get(
            reverse(
                'posts:profile_follow',
                args=[user]
            )
        )
        count_2 = follower.count()
        self.assertTrue(
            follower.exists(),
            'Подписка невозможна'
        )
        self.assertEqual(count_1 + 1, count_2)

    def test_unfollowing(self):
        """Тест отписки от автора."""
        client = self.authorized_author
        user = self.follower
        author = self.author
        follower = Follow.objects.filter(
            user=author,
            author=self.follower
        )
        count_1 = follower.count()
        client.get(
            reverse(
                'posts:profile_unfollow',
                args=[user]
            ),
        )
        count_2 = follower.count()
        self.assertFalse(
            follower,
            'Отписка невозможна'
        )
        self.assertEqual(count_1 - 1, count_2)

    def test_new_post_showing_for_followers(self):
        follow_post = Post.objects.create(
            text='test-text', author=self.author
        )
        self.authorized_follower.get(
            reverse('posts:profile_follow', kwargs={'username': self.author})
        )
        following_count = (
            Follow.objects.filter(author=self.author).count()
        )
        follower_response = (
            self.authorized_follower.get(reverse('posts:follow_index'))
        )
        self.assertEqual(following_count, 1)
        self.assertIn(follow_post, follower_response.context.get('page_obj'))

    def test_new_post_showing_for_unfollowers(self):
        unfollow_post = Post.objects.create(
            text='test-text', author=self.author
        )
        unfollower_response = (
            self.authorized_unfollower.get(reverse('posts:follow_index'))
        )
        self.assertNotIn(
            unfollow_post,
            unfollower_response.context.get('page_obj')
        )
        self.authorized_unfollower.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.author})
        )
        unfollowing_count = Follow.objects.filter(author=self.author).count()
        self.assertEqual(unfollowing_count, 0)
