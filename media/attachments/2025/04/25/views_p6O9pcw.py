from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse

from .models import Post, Comment, Category, Attachment, PostAttachment
from .forms import PostForm, CommentForm
from .utils import date_handler
from django.db.models import Count
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
def post_list(request):
    posts = Post.objects.all().order_by('-created_at')
    categories = Category.objects.annotate(num_posts=Count('post'))
    posts = [date_handler(post) for post in posts]
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # AJAX请求，只返回帖子部分
        posts_html = render_to_string('community/partials/posts_list.html', {'posts': posts})
        return JsonResponse({'posts_html': posts_html})
    context = {
        'posts': posts,
        'categories': categories,
    }
    return render(request, 'community/home.html', context)

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

def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            # 处理附件关联
            attachment_ids = form.cleaned_data.get('attachments', '').split(',')
            valid_ids = [int(id) for id in attachment_ids if id.isdigit()]
            # 通过中间模型关联附件（可以添加额外字段）
            for idx, att_id in enumerate(valid_ids):
                attachment = Attachment.objects.get(id=att_id)
                PostAttachment.objects.create(
                    post=post,
                    attachment=attachment,
                    is_primary=(idx == 0)  # 示例：第一个附件设为主附件
                )
            # return redirect('post-detail', pk=post.pk)
            return JsonResponse({
                'success': True,
                'redirect': reverse('post-detail', kwargs={'pk': post.pk})
            })
    else:
        form = PostForm()
    return render(request, 'community/post_form.html', {'form': form})

@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST, request.FILES)
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
        form = CommentForm(request.POST, request.FILES)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.parent_comment = parent_comment
            comment.save()
    return redirect('post_detail', post_id=post.id)

def is_admin(user):
    return user.is_superuser

@user_passes_test(is_admin)
def delete_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    post_pk = comment.post.pk
    comment.delete()
    return redirect('post_detail', pk=post_pk)

def category_posts(request, slug):
    category = get_object_or_404(Category, slug=slug)
    posts = Post.objects.filter(category=category)
    posts = [date_handler(post) for post in posts]
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # AJAX请求，只返回帖子部分
        posts_html = render_to_string('community/partials/posts_list.html', {'posts': posts})
        return JsonResponse({'posts_html': posts_html})
        # 普通请求，返回完整页面
    return render(request, 'community/home.html', {'posts': posts, 'categories': Category.objects.all()})


@csrf_exempt
def upload_attachment(request):
    if request.method == 'POST' and request.FILES:
        attach_file = request.FILES.get('file')
        response_data = {}
        if attach_file:
            attachment = Attachment.objects.create(
                file=attach_file,
                uploader=request.user,
                description=attach_file.name
            )
            response_data = {
                'id': attachment.id,
                'name': attachment.file.name,
                'url': attachment.file.url,
                'type': attachment.filetype,
                'size': attachment.file.size
            }
        return JsonResponse({'success': True, 'files': response_data})

    return JsonResponse({'success': False, 'error': '无效请求'}, status=400)