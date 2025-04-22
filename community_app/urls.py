# community/urls.py
from django.urls import path
from . import views
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    path('', views.post_list, name='post-list'),
    path('post/<int:pk>/', views.post_detail, name='post-detail'),
    path('post/new/', views.post_create, name='post-create'),
    path('<int:post_id>/add_comment/', views.add_comment, name='add-comment'),
    path('<int:comment_id>/add_reply_to_comment/', views.reply_to_comment, name='add-reply-to-comment'),
]