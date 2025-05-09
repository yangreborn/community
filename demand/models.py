from rest_framework.exceptions import ValidationError
from django.db import models
from django.utils import timezone

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
        'completed': [],
        'rejected': [],
        'cancelled': []
    }
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='posts', verbose_name='分类')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='demands')
    handler = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='handled_demands')
    title = models.CharField('标题', max_length=200)
    description = models.TextField('描述')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    completed_at = models.DateTimeField('完成时间', null=True, blank=True)
    is_able = models.BooleanField(default=True, verbose_name='是否禁用')

    class Meta:
        verbose_name = '需求'
        verbose_name_plural = '需求'
        ordering = ['-created_at']

    def clean(self):
        # 这里实现状态转换的验证逻辑
        old_status = self.__class__.objects.get(pk=self.pk).status if self.pk else None
        if old_status and not self._is_valid_transition(old_status, self.status):
            raise ValidationError(f'不允许从 {old_status} 状态转换到 {self.status} 状态')

    def is_valid_transition(self, new_status):
        """检查状态转换是否合法"""
        return new_status in self.STATUS_TRANSITIONS.get(self.status, [])

    def change_status(self, new_status, user, reason=None):
        """
        变更状态并记录变更历史
        :param new_status: 新状态
        :param user: 执行变更的用户
        :param reason: 变更原因(可选)
        """
        if not self.is_valid_transition(new_status):
            raise ValueError(
                f"Invalid status transition from {self.get_status_display()} to "
                f"{dict(self.STATUS_CHOICES).get(new_status)}"
            )

            # 记录变更前的状态
        from_status = self.status

        # 执行状态变更
        self.status = new_status
        self.updated_at = timezone.now()

        # 如果是完成状态，记录完成时间
        if new_status == 'completed':
            self.completed_at = timezone.now()

        self.save()

        # 记录状态变更历史
        DemandStatusChange.objects.create(
            demand=self,
            from_status=from_status,
            to_status=new_status,
            changed_by=user,
            change_reason=reason
        )

        # 执行状态变更后的额外操作
        self.after_status_change(from_status, new_status, user)

    def after_status_change(self, from_status, to_status, user):
        """
        状态变更后的额外操作
        可以在这里添加通知、日志等逻辑
        """
        # 示例：分配处理人
        if to_status == 'accepted' and not self.handler:
            self.handler = user
            self.save()

        # 示例：发送通知
        self.send_status_notification(to_status, user)

    def send_status_notification(self, new_status, changed_by):
        """
        发送状态变更通知
        实际项目中可以使用 Django 的邮件系统或第三方通知服务
        """
        # 这里只是示例，实际实现根据项目需求
        print(f"通知：需求 '{self.title}' 状态已变更为 {self.get_status_display()}，操作人：{changed_by.username}")

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
