from django.db.models import Q
from rest_framework import serializers
from .models import Category, Post, Comment, PostAttachment, Tag
from .utils import format_created_at
from account.serializers import UserSerializer

class CategorySerializer(serializers.ModelSerializer):
    count = serializers.SerializerMethodField(help_text='分类下帖子数')
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'count', 'parent_id']
        ref_name = 'CommunityCategorySerializer'

    @staticmethod
    def get_count(obj):
        return len(obj.posts.all())

class PostAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostAttachment
        fields = ['id', 'file', 'upload_at']
        read_only_fields = ('upload_at',)

class CommentSerializer(serializers.ModelSerializer):
    formatted_created_at = serializers.SerializerMethodField(help_text='格式化创建时间')
    author_name = serializers.SerializerMethodField()
    author_role = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
                    'id', 'author', 'post', 'content', 'created_at', 'formatted_created_at', 'parent_comment',
                    'author_name', 'author_role'
                  ]
        read_only_fields = ('created_at', 'parent_comment',)
        ref_name = 'CommunityCommentSerializer'

    @staticmethod
    def get_formatted_created_at(obj) -> str:
        return format_created_at(obj.created_at)

    @staticmethod
    def get_author_name(obj):
        return obj.author.username

    @staticmethod
    def get_author_role(obj):
        return obj.author.role

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']

class PostDetailSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    attachments = PostAttachmentSerializer(read_only=True, many=True)
    formatted_created_at = serializers.SerializerMethodField(help_text='格式化创建时间')
    comments = serializers.SerializerMethodField()
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        source='tags',
        read_only=True,
    )
    title = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField(help_text='回复数')
    class Meta:
        model = Post
        fields = [
            'id', 'title', 'content', 'author', 'categories', 'comments', 'tag_ids', 'created_at',
            'updated_at',  'view_count', 'is_pinned', 'attachments', 'formatted_created_at', 'comments_count',
            'is_able', 'fake_author',
        ]
        read_only_fields = ('created_at', 'updated_at', 'author', 'view_count', 'is_able', 'comments_count', )

    @staticmethod
    def get_formatted_created_at(obj) -> str:
        return format_created_at(obj.created_at)

    def get_comments(self, obj):
        request = self.context.get('request')
        comments = obj.comments.all()
        # 未认证用户只能看到已审核的公开回复
        if not request or not request.user.is_authenticated:
            comments = comments.filter(is_create_approved=True, visibility='public').exclude(is_able=False)
        # 认证非管理员用户可以看到已审核公开评论和自己的回复
        elif not request.user.is_staff:
            comments = comments.filter(
                Q(is_create_approved=True, visibility='public') | Q(author=request.user)
            ).exclude(is_able=False)
        return CommentSerializer(comments, many=True, context=self.context).data

    def get_comments_count(self, obj):
        return len(self.get_comments(obj))

    def get_title(self, obj):
        obj._request_user = self.context['request'].user
        return obj.display_title

    def get_content(self, obj):
        # 将请求用户传递给模型
        obj._request_user = self.context['request'].user
        return obj.display_content

class PostCreateOrEditSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
    )

    class Meta:
        model = Post
        fields = ['title', 'content', 'author', 'category', 'category_id', 'created_by', 'fake_author']


