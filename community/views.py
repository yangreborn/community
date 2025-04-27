from django.db.models import F
from django.shortcuts import render
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from account.models import User
from .models import Category, Post, PostAttachment, Comment
from .serializers import (
    UserSerializer, CategorySerializer, PostSerializer,
    CommentSerializer, PostAttachmentSerializer
)
from .permissions import IsOwnerOrAdmin, IsAdminOrReadOnly

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrReadOnly]

class UserRegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrAdmin]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # 使用F()表达式避免竞争条件
        Post.objects.filter(pk=instance.pk).update(view_count=F('view_count') + 1)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    @action(detail=True, methods=['post'])
    def pin(self, request, pk):
        post = self.get_object()
        if not request.user.is_admin():
            return Response({"error":"只有管理员可以置顶"}, status=status.HTTP_403_FORBIDDEN)

        post.is_pinned = not post.is_pinned
        post.save()
        return Response({'status' : '置顶成功' if post.is_pinned else '取消置顶成功'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def upload_attachment(self, request, pk):
        post = self.get_object()
        if post.author != request.user and not request.user.is_admin():
            return Response({'error': '没有上传权限'}, status=status.HTTP_403_FORBIDDEN)

        file = request.FILES.get('file')
        if not file:
            return Response({'error':'没有提供文件'}, status=status.HTTP_400_BAD_REQUEST)
        attachment = PostAttachment.objects.create(post=post, file=file)
        serializer = PostAttachmentSerializer(attachment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrAdmin]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        post_id = self.request.query_params.get('post_id')
        if post_id:
            queryset = queryset.filter(post_id=post_id)
        return queryset