from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Post, Comment
from .forms import PostForm, CommentForm
from .utils import date_handler

def post_list(request):
    posts = Post.objects.all().order_by('-created_at')
    posts = [date_handler(post) for post in posts]
    return render(request, 'community/post_list.html', {'posts': posts})

def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.increase_views()
    post = date_handler(post)
    top_level_comments = Comment.objects.filter(post=post, parent_comment__isnull=True)
    top_level_comments = date_handler(top_level_comments)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            parent_comment_id = request.POST.get('parent_comment_id')
            if parent_comment_id:
                comment.parent_comment = get_object_or_404(Comment, id=parent_comment_id)
            comment.save()
            return redirect('post-detail', pk=post.pk)
    form_textinput = CommentForm(input_type='textinput')
    form_textarea = CommentForm(input_type='textarea')
    context = {
        'post': post,
        'form_textinput': form_textinput,
        'form_textarea': form_textarea,
        'top_level_comments': top_level_comments,
        'comment_count': len(top_level_comments),
    }
    # 增加浏览量
    return render(request, 'community/post_detail.html', context)

@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('post-detail', pk=post.pk)
    else:
        form = PostForm()
    return render(request, 'community/post_form.html', {'form': form})

@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect('post-detail', pk=post.id)

@login_required
def reply_to_comment(request, comment_id):
    parent_comment = get_object_or_404(Comment, id=comment_id)
    post = parent_comment.post

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.parent_comment = parent_comment
            comment.save()
            return redirect('post_detail', post_id=post.id)