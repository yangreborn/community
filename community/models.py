from django.db import models

from account.models import User
# Create your models here.

VISIBILITY_CHOICES = [('private', '仅作者和管理员'), ('public', '公开'),]


class  Category(models.Model):
    name = models.CharField(max_length=20, unique=True, verbose_name='类名')
    description = models.TextField(blank=True, verbose_name='描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    parent_id = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, related_name='children', verbose_name='父类别id')

    class Meta:
        verbose_name = "分类"
        verbose_name_plural = "分类"

    def __str__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='标签名')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "标签"
        verbose_name_plural = "标签"

class Post(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='posts', verbose_name='分类')
    title = models.CharField(max_length=100, null=False, blank=False, verbose_name='标题')
    edited_title = models.CharField(max_length=100, null=True, blank=True, verbose_name='编辑标题')
    content = models.TextField(blank=True, default='', verbose_name='内容')
    edited_content = models.TextField(blank=True, null=True, verbose_name='编辑内容')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='posts', verbose_name='作者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    is_pinned = models.BooleanField(default=False, verbose_name='是否置顶')
    view_count = models.PositiveIntegerField(default=0, verbose_name='浏览量')
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts', verbose_name='标签')
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='private', verbose_name='可视    度')
    is_create_approved = models.BooleanField(default=False, verbose_name='创建帖子审核是否通过')
    is_edit_approved = models.BooleanField(default=True, verbose_name='编辑帖子审核是否通过')
    last_edited_at = models.DateTimeField(null=True, blank=True, verbose_name='最后更新时间')
    is_able = models.BooleanField(default=True, verbose_name='是否禁用')
    fake_author = models.CharField(max_length=100, null=True, blank=True, verbose_name='伪作者')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_posts', default=None, verbose_name='创建人')

    class Meta:
        ordering = ['-is_pinned', '-created_at']
        verbose_name = "帖子"
        verbose_name_plural = "帖子"

    def __str__(self):
        return self.title

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
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', verbose_name='帖子')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='comments', verbose_name='作者')
    content = models.TextField(verbose_name='内容')
    edited_content = models.TextField(null=True, blank=True, verbose_name='编辑内容')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies', verbose_name='父回复')
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='private', verbose_name='可视度')
    is_create_approved = models.BooleanField(default=False, verbose_name='创建回复是否通过')
    is_edit_approved = models.BooleanField(default=True, verbose_name='编辑回复是否通过')
    last_edited_at = models.DateTimeField(null=True, blank=True, verbose_name='最后编辑时间')
    is_able = models.BooleanField(default=True, verbose_name='是否禁用')
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
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='attachments', verbose_name='帖子')
    file = models.FileField(upload_to='post_attachments', verbose_name='文件')
    upload_at = models.DateTimeField(auto_now_add=True, verbose_name='上传时间')

