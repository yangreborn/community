from django.db import models
from account.models import User
# Create your models here.
class Order(models.Model):
    STATUS_CHOICES = (
        ('new', '新建'),
        ('in_progress', '处理中'),
        ('completed', '已完成'),
        ('rejected', '已拒绝'),
    )

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)