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

