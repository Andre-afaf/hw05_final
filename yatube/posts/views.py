from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .utils import get_paginator


def index(request):
    template = 'posts/index.html'
    page_obj, posts_count = get_paginator(Post.objects.all(), request)
    title = 'Главная страница'
    context = {
        'title': title,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    page_obj, posts_count = get_paginator(group.posts.all(), request)
    title = group.title
    context = {
        'group': group,
        'title': title,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    page_obj, posts_count = get_paginator(author.posts.all(), request)
    title = f'Профайл пользователя {author.username}'
    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user,
            author=author).exists()
    context = {
        'author': author,
        'posts_count': posts_count,
        'title': title,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    title = f'Пост {post.text[:30]}'
    author_posts = Post.objects.filter(author=post.author)
    posts_count = author_posts.count()
    image = post.image
    form = CommentForm()
    comments = post.comments.all()
    context = {
        'title': title,
        'post': post,
        'posts_count': posts_count,
        'image': image,
        'form': form,
        'comments': comments
    }
    return render(request, template, context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        form = form.save(commit=False)
        form.author = request.user
        form.save()
        return redirect('posts:profile', form.author)
    template = 'posts/create_post.html'
    context = {
        'form': form,
    }
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post.pk)
    template = 'posts/create_post.html'
    is_edit = True
    context = {
        'form': form,
        'is_edit': is_edit,
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = Post.objects.get(pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj, total_count = get_paginator(posts, request)
    context = {
        'page_obj': page_obj
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    template = 'posts:profile'
    author = get_object_or_404(User, username=username)
    user = request.user
    if user != author:
        Follow.objects.get_or_create(user=user, author=author)
    return redirect(template, username)


@login_required
def profile_unfollow(request, username):
    template = 'posts:profile'
    author = get_object_or_404(User, username=username)
    if author != request.user:
        following = get_object_or_404(
            Follow, user=request.user, author=author
        )
        following.delete()
    return redirect(template, username)
