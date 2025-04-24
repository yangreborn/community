# community/urls.py
from django.urls import path
from . import views
from django.contrib.auth.views import LoginView, LogoutView
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('', views.post_list, name='post-list'),
    path('post/<int:pk>/', views.post_detail, name='post-detail'),
    path('post/new/', views.post_create, name='post-create'),
    path('<int:post_id>/add_comment/', views.add_comment, name='add-comment'),
    path('<int:comment_id>/add_reply_to_comment/', views.reply_to_comment, name='add-reply-to-comment'),
    path('<int:comment_id>/delete_comment/', views.delete_comment, name='delete-comment'),
    path('category/<slug:slug>/', views.category_posts, name='category_posts'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)