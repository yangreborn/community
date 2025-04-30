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
    edited_title = models.CharField(max_length=100, null=True, blank=True)
    content = models.TextField(blank=True, default='')
    edited_content = models.TextField(blank=True, null=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='posts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_pinned = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts')
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='private')
    is_create_approved = models.BooleanField(default=False)
    is_edit_approved = models.BooleanField(default=True)
    last_edited_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        ordering = ['-is_pinned', '-created_at']

    @property
    def display_content(self):
        """根据用户权限返回应显示的内容"""
        if self.is_edit_approved or self._user_has_permission():
            return self.edited_content if self.edited_content else self.content
        return self.content

    @property
    def display_title(self):
        """根据用户权限返回应显示的内容"""
        if self.is_edit_approved or self._user_has_permission():
            return self.edited_title if self.edited_title else self.title
        return self.title

    def _user_has_permission(self, user=None):
        """检查用户是否有权限查看未审核编辑"""
        user = user or getattr(self, '_request_user', None)
        return user and (user.is_staff or user == self.author)


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='comments')
    content = models.TextField()
    edited_content = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='private')
    is_create_approved = models.BooleanField(default=False)
    is_edit_approved = models.BooleanField(default=True)
    last_edited_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        ordering = ['-created_at']

    @property
    def display_content(self):
        if self.is_edit_approved or self._user_has_permission():
            return self.edited_content if self.edited_content else self.content
        return self.content

    def _user_has_permission(self, user=None):
        """检查用户是否有权限查看未审核编辑"""
        user = user or getattr(self, '_request_user', None)
        return user and (user.is_staff or user == self.author)

class PostAttachment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='post_attachments')
    upload_at = models.DateTimeField(auto_now_add=True)

