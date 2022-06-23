import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import CommentForm, PostForm
from posts.models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
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
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст',
            group=cls.group
        )

        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    def test_create_post(self):
        posts_count = Post.objects.count()
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
        form_data = {
            'title': 'Тестовый заголовок',
            'text': 'Тестовый текст',
            'image': uploaded,
        }
        response = self.authorized_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.author.username})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(
            text=form_data['text']).exists()
        )

    def test_edit_post(self):
        post = self.post
        form_data = {
            'text': 'Другой тестовый текст'
        }
        self.authorized_author.post(
            reverse('posts:post_edit', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True
        )
        post_new = Post.objects.get(id=post.pk)
        self.assertNotEqual(post.text, post_new.text)


class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Гениальный пост',
        )
        cls.form = CommentForm()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_add_comment(self):
        comment_url = reverse(
            'posts:add_comment', kwargs={'post_id': self.post.pk}
        )
        post_details_url = reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk}
        )
        form_data = {
            'text': 'Тестовый комментарий',
            'post': self.post
        }
        response = self.authorized_client.post(
            comment_url,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, post_details_url)
        self.assertTrue(
            Comment.objects.filter(
                text='Тестовый комментарий',
                post=self.post,
            ).exists()
        )
