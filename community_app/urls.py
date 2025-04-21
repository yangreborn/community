# community/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.post_list, name='post-list'),
    path('post/<int:pk>/', views.post_detail, name='post-detail'),
    path('post/new/', views.post_create, name='post-create'),
    path('<int:post_id>/add_comment/', views.add_comment, name='add-comment'),
]