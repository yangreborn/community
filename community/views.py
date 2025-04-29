from django.db.models import F, Q, Count
from rest_framework import filters
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from account.models import User
from .models import Category, Post, PostAttachment, Comment, Tag
from .serializers import (
    UserSerializer, CategorySerializer, PostSerializer,
    CommentSerializer, PostAttachmentSerializer, TagSerializer
)
from .permissions import IsOwnerOrAdmin, IsOwnerAdminOrApproved, IsAdminUser

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsOwnerOrAdmin]

class UserRegisterView(GenericAPIView):
    serializer_class = UserSerializer
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsOwnerOrAdmin]

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ['title', 'content', 'author__username']
    ordering_fields = ('created_at', )
    ordering = ('-created_at',)
    permission_classes = [IsOwnerAdminOrApproved, IsOwnerOrAdmin]

    def get_queryset(self):
        queryset = super().get_queryset()
        # 未认证用户只能看到已审核的公开内容
        if not self.request.user.is_authenticated:
            return queryset.filter(approved=True, visibility='public')
        # 认证用户可以看到自己的内容和已审核的公开内容
        if not self.request.user.is_staff:
            return queryset.filter(
                (Q(approved=True, visibility='public') | Q(author=self.request.user))
            )
            # 管理员可以看到所有内容
        return queryset

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

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def approve(self, request, pk=None):
        """帖子审核通过"""
        post = self.get_object()
        post.approved = True
        post.visibility = 'public'
        post.save()
        return Response({'status': '帖子已审核通过'})

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reject(self, request, pk=None):
        """帖子审核驳回"""
        post = self.get_object()
        post.approved = False
        post.visibility = 'private'
        post.save()
        return Response({'status': '帖子已拒绝'})

    @action(detail=True, methods=['post', 'delete'])
    def tags(self, request, pk=None):
        """帖子标签的增删"""
        post = self.get_object()
        if request.method == 'POST':
            # 添加标签
            tag_ids = request.data.get('tag_ids', [])
            if not isinstance(tag_ids, list):
                tag_ids = [tag_ids]

            tags = Tag.objects.filter(id__in=tag_ids)
            post.tags.add(*tags)
            return Response({'status': '标签添加成功'})
        elif request.method == 'DELETE':
            # 移除标签
            tag_ids = request.data.get('tag_ids', [])
            if not isinstance(tag_ids, list):
                tag_ids = [tag_ids]

            post.tags.remove(*tag_ids)
            return Response({'status': '标签移除成功'})

    @action(detail=True, methods=['get'])
    def related(self, request, pk=None):
        """基于标签的相关帖子推荐"""
        post = self.get_object()
        # 获取共享至少一个标签的帖子，按共享标签数排序
        related_posts = Post.objects.filter(
            tags__in=post.tags.all()
        ).exclude(
            id=post.id
        ).annotate(
            common_tags=Count('tags')
        ).order_by(
            '-common_tags',
            '-created_at'
        )[:5]  # 限制返回数量
        serializer = self.get_serializer(related_posts, many=True)
        return Response(serializer.data)

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsOwnerAdminOrApproved, IsOwnerOrAdmin]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        # 未认证用户只能看到已审核的公开内容
        if not self.request.user.is_authenticated:
            return queryset.filter(approved=True, visibility='public')
        # 认证用户可以看到自己的内容和已审核的公开内容
        if not self.request.user.is_staff:
            return queryset.filter(
                Q(approved=True, visibility='public') |
                Q(author=self.request.user))
            # 管理员可以看到所有内容
        return queryset

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def approve(self, request, pk=None):
        post = self.get_object()
        post.approved = True
        post.visibility = 'public'
        post.save()
        return Response({'status': '回复1已审核通过'})

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reject(self, request):
        post = self.get_object()
        post.approved = False
        post.save()
        return Response({'status': '回复已拒绝'})

class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAdminUser]