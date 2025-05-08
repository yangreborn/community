from django.utils import timezone
from django.db.models import F, Q, Count
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import filters
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from account.models import User
from .models import Category, Post, PostAttachment, Comment, Tag
from .serializers import (
    UserSerializer, CategorySerializer, PostDetailSerializer,
    CommentSerializer, PostAttachmentSerializer, TagSerializer, PostCreateOrEditSerializer
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

class CustomPageNumberPagination(PageNumberPagination):
    page_size = 10  # 每页显示的记录数
    page_size_query_param = 'page_size'  # 允许客户端通过该参数指定每页显示的记录数
    max_page_size = 100  # 每页最大显示的记录数

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUser]

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    filter_backends = (filters.SearchFilter, )
    search_fields = ['title', 'content', 'author__username']
    permission_classes = [IsOwnerAdminOrApproved, IsOwnerOrAdmin]
    pagination_class = CustomPageNumberPagination

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return PostCreateOrEditSerializer
        return PostDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        #检查是否是请求未回复帖子列表的特殊情况
        is_unreplied_endpoint = getattr(self, 'action', None) == 'unreplied'

        # 未认证用户只能看到已审核的公开内容
        if not self.request.user.is_authenticated:
            return queryset.filter(is_create_approved=True, visibility='public').exclude(is_able=False)

        # 管理员查看未回复帖子
        if is_unreplied_endpoint and self.request.user.is_staff:
            # 获取所有有管理员回复的帖子ID
            replied_post_ids = Comment.objects.filter(
                author__is_staff=True
            ).exclude(is_able=False).values_list('post_id', flat=True).distinct()

            # 返回未被管理员回复的帖子（排除管理员自己发的帖子）
            return queryset.exclude(
                Q(id__in=replied_post_ids) | Q(author__is_staff=True)
            ).filter(
                is_create_approved=True  # 可选：只显示已审核的帖子
            ).exclude(is_able=False)

        # 普通认证用户可以看到自己的内容和已审核的公开内容
        if not self.request.user.is_staff:
            return queryset.filter(
                Q(is_create_approved=True, visibility='public') | Q(author=self.request.user)
            ).exclude(is_able=False)
        return queryset

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        post = self.get_object()
        if not IsOwnerOrAdmin().has_object_permission(request, self, post):
            return Response({'error': '没有权限编辑此对象'}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(post, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        post.edited_title = serializer.validated_data.get('title')
        post.edited_content = serializer.validated_data.get('content')
        post.last_edited_at = timezone.now()
        post.is_edit_approved = False
        post.save()
        return Response(
            {'status': '编辑请求已提交，等待审核'},
            status=status.HTTP_202_ACCEPTED
        )

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
        serializer.save(author=self.request.user, created_by=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # 使用F()表达式避免竞争条件
        Post.objects.filter(pk=instance.pk).update(view_count=F('view_count') + 1)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

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

    @swagger_auto_schema(
        method='get',
        operation_summary=' 获取未审批的帖子',
        operation_description='''
                    用于获取管理员未审批的帖子
                    参数：无
                    权限：管理员
                '''
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def unapproved(self, request):
        """
        获取未审批且可用的对象列表，管理员权限
        """
        queryset = self.filter_queryset(self.get_queryset()).filter(is_create_approved=False, is_able=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        method='post',
        operation_summary='置顶帖子',
        operation_description='''
                        未置顶设为置顶，已置顶取消置顶，id为帖子id
                        参数：无
                        权限：管理员
                    '''
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def pin(self, request, pk):
        """
        未置顶设为置顶，已置顶取消置顶，管理员权限
        """
        post = self.get_object()
        post.is_pinned = not post.is_pinned
        post.save()
        return Response({'status' : '置顶成功' if post.is_pinned else '取消置顶成功'}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        method='post',
        operation_summary='上传附件',
        operation_description='''
                            上传附件
                            参数：file: 文件类型，必需参数。要上传的附件文件。
                            权限：管理员和作者
                        '''
    )
    @action(detail=True, methods=['post'], permission_classes=[IsOwnerOrAdmin])
    def upload_attachment(self, request, pk):
        """
        上传附件，管理员和作者权限
        """
        post = self.get_object()
        if post.author != request.user and not request.user.is_admin():
            return Response({'error': '没有上传权限'}, status=status.HTTP_403_FORBIDDEN)
        file = request.FILES.get('file')
        if not file:
            return Response({'error':'没有提供文件'}, status=status.HTTP_400_BAD_REQUEST)
        attachment = PostAttachment.objects.create(post=post, file=file)
        serializer = PostAttachmentSerializer(attachment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        method='post',
        operation_summary='帖子创建审核通过',
        operation_description='''
                                帖子创建审核通过，id为帖子id
                                权限：管理员
                            '''
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def create_approve(self, request, pk=None):
        """
        创建帖子审核通过，管理员权限
        """
        post = self.get_object()
        post.is_create_approved = True
        post.visibility = 'public'
        post.save()
        return Response({'status': '帖子已审核通过'})

    @swagger_auto_schema(
        method='post',
        operation_summary='帖子创建审核拒绝',
        operation_description='''
                                    帖子创建审核拒绝，id为帖子id
                                    权限：管理员
                                '''
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def create_reject(self, request, pk=None):
        """
        创建帖子审核驳回，管理员权限
        """
        post = self.get_object()
        post.is_create_approved = False
        post.visibility = 'private'
        post.save()
        return Response({'status': '帖子已拒绝'})

    @swagger_auto_schema(
        method='post',
        operation_summary='帖子编辑审核通过',
        operation_description='''
                                    帖子编辑审核通过，id为帖子id
                                    权限：管理员
                                '''
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def edit_approve(self, request, pk=None):
        """
        编辑帖子审核通过，管理员权限
        """
        post = self.get_object()
        if not post.edited_content and not post.edited_title:
            return Response({'error': '该帖子没有待审核的编辑'}, status=400)
        # 批准编辑
        post.title = post.edited_title if post.edited_title else post.title
        post.content = post.edited_content if post.edited_content else post.content
        post.edited_title = None
        post.edited_content = None
        post.is_edit_approved = True
        post.save()
        return Response({'status': '编辑已批准'})

    @swagger_auto_schema(
        method='post',
        operation_summary='帖子编辑审核拒绝',
        operation_description='''
                                    帖子编辑审核拒绝，id为帖子id
                                    权限：管理员
                                '''
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def edit_reject(self, request, pk=None):
        """
        编辑帖子审核驳回，管理员权限
        """
        post = self.get_object()
        if not post.edited_content and not post.edited_title:
            return Response({'error': '该帖子没有待审核的编辑'}, status=400)
        # 批准编辑
        post.is_edit_approved = False
        post.save()
        return Response({'status': '编辑已拒绝'})

    @swagger_auto_schema(
        methods= ['post', 'delete'],
        operation_summary='新增删除帖子标签',
        operation_description='''
                            post新增帖子标签，delete删除帖子标签，id为帖子id
                            - tag_ids: 数组类型，必需参数。要操作的标签 ID 列表。可以是单个 ID 或多个 ID 组成的数组。
                            权限：管理员
                            '''
    )
    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAdminUser])
    def tags(self, request, pk=None):
        """
        新增，删除帖子标签，管理员权限
        """
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

    @swagger_auto_schema(
        method='get',
        operation_summary='获取帖子相关推荐',
        operation_description='''
                                获取帖子的相关推荐帖子，id为帖子id
                                权限：无
                                '''
    )
    @action(detail=True, methods=['get'])
    def related(self, request, pk=None):
        """
        获取帖子的相关推荐帖子
        """
        post = self.get_object()
        # 获取共享至少一个标签的帖子，按共享标签数排序
        related_posts = Post.objects.filter(
            Q(is_create_approved=True, visibility='public') &
            Q(tags__in=post.tags.all())
        ).exclude(
            id=post.id, is_able=False
        ).annotate(
            common_tags=Count('tags')
        ).order_by(
            '-common_tags',
            '-created_at'
        )[:5]  # 限制返回数量
        serializer = self.get_serializer(related_posts, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        method='post',
        operation_summary='创建伪帖子',
        operation_description='''
                                管理员创建伪作者帖子，
                                参数：
                                - title: 字符串类型，必须参数。帖子标题。
                                - content: 字符串类型，可选参数。帖子内容。
                                - category_id: 整数类型，必选参数。帖子分类的id
                                权限：管理员
                                '''
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def create_fake_post(self, request):
        """
        创建伪作者帖子，管理员权限
        """
        serializer = PostCreateOrEditSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

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
            return queryset.filter(is_create_approved=True, visibility='public')
        # 认证用户可以看到自己的内容和已审核的公开内容
        if not self.request.user.is_staff:
            return queryset.filter(
                Q(is_create_approved=True, visibility='public') |
                Q(author=self.request.user)).exclude(is_able=False)
            # 管理员可以看到所有内容
        return queryset

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        post = self.get_object()
        if not IsOwnerOrAdmin().has_object_permission(request, self, post):
            return Response({'error': '没有权限编辑此对象'}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(post, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        post.edited_content = serializer.validated_data.get('content')
        post.last_edited_at = timezone.now()
        post.is_edit_approved = False
        post.save()
        return Response(
            {'status': '编辑请求已提交，等待审核'},
            status=status.HTTP_202_ACCEPTED
        )

    @swagger_auto_schema(
        method='post',
        operation_summary='回复创建审核通过',
        operation_description='''
                                    回复创建审核通过，id为回复id
                                    权限：管理员
                                '''
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def create_approve(self, request, pk=None):
        """
        创建回复审核通过，管理员权限
        """
        comment = self.get_object()
        comment.is_create_approved = True
        comment.visibility = 'public'
        comment.save()
        return Response({'status': '回复已审核通过'})

    @swagger_auto_schema(
        method='post',
        operation_summary='回复创建审核拒绝',
        operation_description='''
                                        回复创建审核拒绝，id为回复id
                                        权限：管理员
                                    '''
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def create_reject(self, request):
        """
        创建回复审核驳回，管理员权限
        """
        comment = self.get_object()
        comment.is_create_approved = False
        comment.visibility = 'private'
        comment.save()
        return Response({'status': '回复已拒绝'})

    @swagger_auto_schema(
        method='post',
        operation_summary='回复编辑审核通过',
        operation_description='''
                                        回复编辑审核通过，id为回复id
                                        权限：管理员
                                    '''
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def edit_approve(self, request, pk=None):
        """
        编辑回复审核通过，管理员权限
        """
        comment = self.get_object()
        if not comment.edited_content:
            return Response({'error': '该回复没有待审核的编辑'}, status=400)
        # 批准编辑
        comment.content = comment.edited_content if comment.edited_content else comment.content
        comment.edited_content = None
        comment.is_edit_approved = True
        comment.save()
        return Response({'status': '编辑已批准'})

    @swagger_auto_schema(
        method='post',
        operation_summary='回复编辑审核拒绝',
        operation_description='''
                                            回复编辑审核拒绝，id为回复id
                                            权限：管理员
                                        '''
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def edit_reject(self, request, pk=None):
        """
        编辑回复审核驳回，管理员权限
        """
        comment = self.get_object()
        if not comment.edited_content:
            return Response({'error': '该回复没有待审核的编辑'}, status=400)
        # 批准编辑
        comment.is_edit_approved = False
        comment.save()
        return Response({'status': '编辑已拒绝'})

class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAdminUser]
