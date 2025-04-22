# community/forms.py
from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content']
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
        fields = ['content']
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