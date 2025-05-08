from django.urls import path, include
from rest_framework.routers import DefaultRouter
from account.views import UserViewSet, UserRegisterView
from community.views import PostViewSet, CategoryViewSet, CommentViewSet, TagViewSet

router = DefaultRouter()
router.register('posts', PostViewSet)
router.register('categories', CategoryViewSet)
router.register('comments', CommentViewSet)
router.register('tags', TagViewSet)
urlpatterns = [
    path('', include(router.urls)),

]