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
        ('draft', '草稿'),  # 用户创建但未正式提交的需求，可自由编辑和删除
        ('submitted', '已提交'),  # 用户正式提交的需求，等待管理员/负责人处理
        ('accepted', '已受理'),  # 管理员确认需求有效并接受处理，分配负责人或团队
        ('in_progress', '处理中'),  # 需求正在被实施或解决，可更新进度和子任务
        ('pending_review', '待反馈'),  # 阶段性成果等待用户确认，用户验收或提出修改意见
        ('completed', '已完成'),  # 需求已实现并通过最终验收，可归档或转为知识库条目
        ('rejected', '已拒绝'),  # 管理员判定为无效或不合理需求，需提供拒绝理由
        ('on_hold', '已暂停'),  # 因某些原因暂时搁置的需求，可随时恢复处理
        ('cancelled', '已取消'),  # 用户或管理员主动取消的需求，区分用户取消和系统取消
    )
    STATUS_TRANSITIONS = {
        'draft': ['submitted', 'cancelled'],
        'submitted': ['accepted', 'rejected', 'cancelled'],
        'accepted': ['in_progress', 'cancelled'],
        'in_progress': ['pending_review', 'on_hold', 'cancelled'],
        'pending_review': ['in_progress', 'completed'],
        'on_hold': ['in_progress', 'cancelled'],
        # 终止状态不可再转换
        'completed': [],
        'rejected': [],
        'cancelled': []
    }
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

    def is_valid_transition(self, new_status):
        """检查状态转换是否合法"""
        return new_status in self.STATUS_TRANSITIONS.get(self.status, [])

    def save(self, *args, **kwargs):
        if self.pk:  # 检查是否是已有实例
            old = Demand.objects.get(pk=self.pk)
            if old.status != self.status:
                DemandStatusChange.objects.create(
                    demand=self,
                    from_status=old.status,
                    to_status=self.status,
                    changed_by=getattr(self, '_status_change_user', None),
                    change_reason=getattr(self, '_status_change_reason', None)
                )
        super().save(*args, **kwargs)

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


class DemandStatusChange(models.Model):
    """
    需求状态变更记录模型
    """
    demand = models.ForeignKey('Demand', on_delete=models.CASCADE, related_name='status_changes')
    from_status = models.CharField(max_length=20)
    to_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    change_reason = models.TextField(blank=True, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']
        verbose_name = '状态变更记录'
        verbose_name_plural = '状态变更记录'

    def __str__(self):
        return f"{self.demand.title}: {self.from_status} → {self.to_status}"
