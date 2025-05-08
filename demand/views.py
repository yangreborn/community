from django.db.models import F, Q, Count
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from .models import Category, Demand, Comment
from .serializers import (
     CategorySerializer, DemandSerializer,
    CommentSerializer,
)
from .permissions import IsOwnerOrAdmin, IsOwnerAdminOrApproved, IsAdminUser

class CustomPageNumberPagination(PageNumberPagination):
    page_size = 10  # 每页显示的记录数
    page_size_query_param = 'page_size'  # 允许客户端通过该参数指定每页显示的记录数
    max_page_size = 100  # 每页最大显示的记录数

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUser]

class DemandViewSet(viewsets.ModelViewSet):
    queryset = Demand.objects.all()
    filter_backends = (filters.SearchFilter, )
    search_fields = ['title', 'content', 'author__username']
    permission_classes = [IsOwnerAdminOrApproved, IsOwnerOrAdmin]
    pagination_class = CustomPageNumberPagination
    serializer_class = DemandSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_authenticated:
            return queryset.none()
        #检查是否是请求未回复帖子列表的特殊情况
        is_unreplied_endpoint = getattr(self, 'action', None) == 'unreplied'
        # 管理员查看未回复帖子
        if is_unreplied_endpoint and self.request.user.is_staff:
            # 获取所有有管理员回复的帖子ID
            replied_ids = Comment.objects.filter(
                author__is_staff=True
            ).exclude(is_able=False).values_list('demand_id', flat=True).distinct()
            # 返回未被管理员回复的帖子（排除管理员自己发的帖子）
            return queryset.exclude(
                Q(id__in=replied_ids) | Q(author__is_staff=True)
            ).exclude(is_able=False)

        # 普通认证用户可以看到自己的内容和已审核的公开内容
        if not self.request.user.is_staff:
            return queryset.filter(
                Q(author=self.request.user)
            ).exclude(is_able=False)
        return queryset

    def destroy(self, request, *args, **kwargs):
        """
        删除帖子，管理员或作者权限
        """
        instance = self.get_object()
        # 检查是否有特定的权限
        if request.user.is_staff or request.user == instance.author:
            # 执行删除操作
            instance.save(is_able=False)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"detail": "You do not have permission to delete this book."},
                            status=status.HTTP_403_FORBIDDEN)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @swagger_auto_schema(
        method='get',
        operation_summary=' 获取未回复的帖子',
        operation_description='''
                用于获取管理员未回复的帖子
                参数：无
                权限：管理员
            '''
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def unreplied(self, request):
        """
        获取未回复的数据列表，管理员权限
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def update_status(self, request, pk=None):
        demand = self.get_object()
        new_status = request.data.get('status')

        if new_status not in dict(demand.STATUS_CHOICES).keys():
            return Response({'error': '无效的状态'}, status=status.HTTP_400_BAD_REQUEST)

        demand.status = new_status
        demand.save()
        return Response({'status': '状态更新成功'})

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsOwnerAdminOrApproved, IsOwnerOrAdmin]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_authenticated:
            return queryset.none()
        # 认证用户可以看到自己的内容和已审核的公开内容
        if not self.request.user.is_staff:
            return queryset.filter(
                Q(author=self.request.user)).exclude(is_able=False)
            # 管理员可以看到所有内容
        return queryset
