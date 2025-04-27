from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.
class User(AbstractUser):
    ROLES = (
        ('admin', '管理员'),
        ('user', '普通用户'),
    )
    role = models.CharField(max_length=10, choices=ROLES, default='user')

    def is_admin(self):
        return self.role == 'admin'

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'