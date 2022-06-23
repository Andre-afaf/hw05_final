from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост. 1617181920',
        )

    def test_models_have_correct_object_names(self):
        """Значение поля __str__ в моделях отображается правильно."""
        post_test = {
            PostModelTest.post: self.post.text[:15],
            PostModelTest.group: self.group.title
        }
        for value, exp_str in post_test.items():
            with self.subTest(value=value):
                self.assertEqual(str(value), exp_str)
