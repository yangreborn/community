from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import  Category, Post, Comment
from django.conf import settings
from account.models import User

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_admin', 'is_staff')
    list_filter = ('is_admin', 'is_staff')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('个人信息', {'fields': ('first_name', 'last_name', 'email')}),
        ('权限', {'fields': ('is_active', 'is_staff', 'is_admin', 'is_superuser', 'groups', 'user_permissions')}),
        ('重要日期', {'fields': ('last_login', 'date_joined')}),
    )

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

