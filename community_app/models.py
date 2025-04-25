from django.db import models

# Create your models here.
# community/models.py
import os
from django.db import models
from django.conf import settings
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.db.models.signals import m2m_changed


class Attachment(models.Model):
    file = models.FileField(upload_to='attachments/%Y/%m/%d/')
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=200, blank=True)

    # 自动获取文件类型
    @property
    def filetype(self):
        return self.file.name.split('.')[-1].lower()

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
    attachments = models.ManyToManyField(Attachment, through='PostAttachment')

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
    attachments = models.ManyToManyField(Attachment, through='CommentAttachment')

    def __str__(self):
        return f"{self.author}在'{self.post}'的评论"

# 中间模型可添加额外关系字段
class PostAttachment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    attachment = models.ForeignKey(Attachment, on_delete=models.CASCADE)
 # 示例扩展字段

class CommentAttachment(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    attachment = models.ForeignKey(Attachment, on_delete=models.CASCADE)

@receiver(post_delete, sender=Attachment)
def auto_delete_file(sender, instance, **kwargs):
    """自动删除实际文件"""
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)

@receiver(m2m_changed, sender=Post.attachments.through)
def cleanup_orphan_attachments(sender, instance, action, **kwargs):
    """清理无关联的附件"""
    if action == 'post_remove':
        Attachment.objects.filter(
            id__in=kwargs['pk_set'],
            post__isnull=True,
            comment__isnull=True
        ).delete()