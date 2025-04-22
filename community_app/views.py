from .utils import date_handler
# Create your views here.
# community/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Post, Comment
from .forms import PostForm, CommentForm
from django.utils import timezone

def post_list(request):
    posts = Post.objects.all().order_by('-created_at')
    posts = [date_handler(post, post.created_at) for post in posts]
    return render(request, 'community/post_list.html', {'posts': posts})

def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.increase_views()
    top_level_comments = Comment.objects.filter(post=post, parent_comment__isnull=True)
    now = timezone.now()
    for comment in top_level_comments:
        # 处理顶级评论的时间显示
        delta = now - comment.created_at
        if delta.days < 7:
            comment.display_time = f"{delta.days} 日内" if delta.days else f"24小时内"
        else:
            comment.display_time = comment.created_at.strftime("%m-%d")
        comment.replies_ = []
        for reply in comment.replies.all():

            # 处理一级回复的时间显示
            delta = now - reply.created_at
            if delta.days < 7:
                reply.display_time = f"{delta.days} 日内" if delta.days else f"24小时内"
            else:
                reply.display_time = reply.created_at.strftime("%m-%d")
            comment.replies_.append(reply)

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
