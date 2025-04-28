from django.db import models
from django.db.models import ForeignKey

from account.models import User
# Create your models here.

VISIBILITY_CHOICES = [('private', '仅作者和管理员'), ('public', '公开'),]


class  Category(models.Model):
    name = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    parent_id = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, related_name='children')

    class Meta:
        verbose_name_plural = "分类"

    def __str__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Post(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='posts')
    title = models.CharField(max_length=100)
    content = models.TextField(blank=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='posts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_pinned = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts')
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='private')
    approved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-is_pinned', '-created_at']

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='private')
    approved = models.BooleanField(default=False)
    class Meta:
        ordering = ['-created_at']

class PostAttachment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='post_attachments')
    upload_at = models.DateTimeField(auto_now_add=True)

