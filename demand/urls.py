from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DemandViewSet, CategoryViewSet, CommentViewSet

router = DefaultRouter()
router.register('demands', DemandViewSet)
router.register('categories', CategoryViewSet)
router.register('comments', CommentViewSet)
urlpatterns = [
    path('', include(router.urls)),
]