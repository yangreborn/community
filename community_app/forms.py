# community/forms.py
import os
from django import forms
from django.core.exceptions import  ValidationError
from django.conf import settings
from .models import Post, Comment

def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1][1:].lower()
    if ext not in settings.ALLOWED_FILE_EXTENSIONS:
        raise ValidationError(f'不支持的文件类型。允许的类型: {", ".join(settings.ALLOWED_FILE_EXTENSIONS)}')

def validate_file_size(value):
    if value.size > settings.MAX_UPLOAD_SIZE:
        raise ValidationError(f'文件太大。最大允许大小: {settings.MAX_UPLOAD_SIZE/1024/1024}MB')


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'category', 'attachments']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'border border-gray-300 rounded-md p-2 w-full focus:ring-blue-500 focus:border-blue-500'
            }),
            'content': forms.Textarea(attrs={
                'class': 'border border-gray-300 rounded-md p-2 w-full focus:ring-blue-500 focus:border-blue-500'
            })
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content', 'attachments']
        widgets = {
            'content': forms.TextInput(attrs={
                'class': 'border border-gray-300 rounded-md p-2 w-full focus:ring-blue-500 focus:border-blue-500'
            }),
        }

    def __init__(self, *args, **kwargs):
        # 获取额外的参数，用于区分不同的情况
        input_type = kwargs.pop('input_type', 'default')
        super().__init__(*args, **kwargs)

        if input_type == 'textarea':
            # 使用 Textarea 输入框
            self.fields['content'].widget = forms.Textarea(attrs={
                'class': 'border border-gray-300 rounded-md p-2 w-full focus:ring-blue-500 focus:border-blue-500',
                'rows': 4  # 设置行数
            })
        else:
            # 默认使用 TextInput 输入框
            self.fields['content'].widget = forms.TextInput(attrs={
                'class': 'border border-gray-300 rounded-md p-2 w-full focus:ring-blue-500 focus:border-blue-500'
            })