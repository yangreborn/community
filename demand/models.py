from django.db import models
from account.models import User


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

class Demand(models.Model):
    STATUS_CHOICES = (
        ('new', '新建'),
        ('in_progress', '处理中'),
        ('completed', '已完成'),
        ('rejected', '已拒绝'),
    )
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='posts', verbose_name='分类')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='demands')
    title = models.CharField('标题', max_length=200)
    description = models.TextField('描述')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    is_able = models.BooleanField(default=True, verbose_name='是否禁用')

    class Meta:
        verbose_name = '需求'
        verbose_name_plural = '需求'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

class Comment(models.Model):
    demand = models.ForeignKey(Demand, on_delete=models.CASCADE, related_name='comments', verbose_name='帖子')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='demand_comments', verbose_name='作者')
    content = models.TextField(verbose_name='内容')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies', verbose_name='父回复')
    last_edited_at = models.DateTimeField(null=True, blank=True, verbose_name='最后编辑时间')
    is_able = models.BooleanField(default=True, verbose_name='是否禁用')
    class Meta:
        ordering = ['-created_at']
