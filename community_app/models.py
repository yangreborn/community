from django.db import models

# Create your models here.
# community/models.py
import os
from django.db import models
from django.conf import settings


def upload_to(instance, filename):
    return f'attachments/{instance.__class__.__name__.lower()}/{filename}'

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='分类名称')
    slug = models.SlugField(max_length=100, unique=True, verbose_name='URL标识', default="wtfk")

    class Meta:
        verbose_name = '分类'
        verbose_name_plural = '分类'

    def __str__(self):
        return self.name

class Post(models.Model):
    title = models.CharField(max_length=200, verbose_name="标题")
    content = models.TextField(verbose_name="内容")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="作者")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    views = models.PositiveIntegerField(default=0, verbose_name="浏览量")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, verbose_name="分类")
    attachments = models.FileField(upload_to='post_attachments/', blank=True, null=True)

    class Meta:
        verbose_name = "帖子"
        verbose_name_plural = "帖子"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def increase_views(self):
        self.views += 1
        self.save(update_fields=['views'])

# models.py
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField(verbose_name="")
    created_at = models.DateTimeField(auto_now_add=True)
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    attachments = models.FileField(upload_to='comment_attachments/', blank=True, null=True)

    def __str__(self):
        return f"{self.author}在'{self.post}'的评论"

