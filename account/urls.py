from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter
from account.views import UserViewSet, UserRegisterView
router = DefaultRouter()
router.register('users', UserViewSet)
urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('check_login/', views.check_login, name='check-login'),
    path('register/', UserRegisterView.as_view(), name='register'),
    path('auth/', include('rest_framework.urls', namespace='rest_framework')),
]
