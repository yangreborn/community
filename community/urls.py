from django.urls import path, include
from rest_framework.routers import DefaultRouter
from community.views import PostViewSet, CategoryViewSet, CommentViewSet, UserViewSet, UserRegisterView, TagViewSet

router = DefaultRouter()
router.register('users', UserViewSet)
router.register('posts', PostViewSet)
router.register('categories', CategoryViewSet)
router.register('comments', CommentViewSet)
router.register('tags', TagViewSet)
urlpatterns = [
    path('', include(router.urls)),
    path('register/', UserRegisterView.as_view(), name='register'),
    path('auth/', include('rest_framework.urls', namespace='rest_framework')),
]