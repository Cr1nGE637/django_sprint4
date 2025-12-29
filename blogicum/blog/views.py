from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .forms import PostForm, CommentForm, UserRegistrationForm, UserEditForm
from .models import Post, Category, Comment

User = get_user_model()


def index(request):
    post_list = Post.objects.select_related(
        'category', 'location', 'author'
    ).filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=timezone.now()
    ).exclude(
        category__isnull=True
    ).annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date')
    
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {'page_obj': page_obj}
    return render(request, 'blog/index.html', context)


def post_detail(request, id):
    post = get_object_or_404(
        Post.objects.select_related('category', 'location', 'author'),
        id=id
    )
    
    # Check if post should be visible to current user
    is_author = request.user.is_authenticated and request.user == post.author
    is_published = (
        post.is_published and 
        (post.category is None or post.category.is_published) and 
        post.pub_date <= timezone.now()
    )
    
    # Only show published posts to non-authors
    # Return 404 for non-authors trying to access unpublished posts
    if not is_published and not is_author:
        raise Http404("Post not found")
    
    comments = post.comments.all().order_by('created_at')
    
    context = {
        'post': post,
        'comments': comments,
        'form': CommentForm() if request.user.is_authenticated else None
    }
    return render(request, 'blog/detail.html', context)


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )
    post_list = Post.objects.select_related(
        'category', 'location', 'author'
    ).filter(
        category=category,
        is_published=True,
        pub_date__lte=timezone.now()
    ).annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date')
    
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'page_obj': page_obj
    }
    return render(request, 'blog/category.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = Post.objects.select_related(
        'category', 'location', 'author'
    ).filter(
        author=author
    ).annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date')
    
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'profile': author,
        'page_obj': page_obj,
    }
    return render(request, 'blog/profile.html', context)


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('blog:profile', username=request.user.username)
    else:
        form = UserEditForm(instance=request.user)
    
    return render(request, 'blog/user.html', {'form': form})


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('blog:profile', username=request.user.username)
    else:
        form = PostForm()
    
    return render(request, 'blog/create.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    if post.author != request.user:
        return redirect('blog:post_detail', id=post_id)
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('blog:post_detail', id=post_id)
    else:
        form = PostForm(instance=post)
    
    return render(request, 'blog/create.html', {'form': form})


@login_required
@require_http_methods(['GET', 'POST'])
def post_delete(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    if post.author != request.user:
        return redirect('blog:post_detail', id=post_id)
    
    if request.method == 'POST':
        post.delete()
        return redirect('blog:profile', username=request.user.username)
    
    form = PostForm(instance=post)
    return render(request, 'blog/create.html', {'form': form})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    
    return redirect('blog:post_detail', id=post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)
    
    if comment.author != request.user:
        return redirect('blog:post_detail', id=post_id)
    
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', id=post_id)
    else:
        form = CommentForm(instance=comment)
    
    return render(request, 'blog/comment.html', {'form': form, 'comment': comment})


@login_required
@require_http_methods(['GET', 'POST'])
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)
    
    if comment.author != request.user:
        return redirect('blog:post_detail', id=post_id)
    
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', id=post_id)
    
    return render(request, 'blog/comment.html', {'comment': comment})


def registration(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect('login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'registration/registration_form.html', {'form': form})

