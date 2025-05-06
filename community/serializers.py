from django.db.models import Q
from rest_framework import serializers
from account.models import User
from .models import Category, Post, Comment, PostAttachment, Tag
from .utils import format_created_at

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'role', 'password')
        read_only_fields = ('role',)
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        return user

class CategorySerializer(serializers.ModelSerializer):
    count = serializers.SerializerMethodField()
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'count', 'parent_id']

    @staticmethod
    def get_count(obj):
        return len(obj.posts.all())

class PostAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostAttachment
        fields = ['id', 'file', 'upload_at']
        read_only_fields = ('upload_at',)

class CommentSerializer(serializers.ModelSerializer):
    formatted_created_at = serializers.SerializerMethodField()
    class Meta:
        model = Comment
        fields = ['id', 'author', 'post', 'content', 'created_at', 'formatted_created_at']
        read_only_fields = ('created_at',)

    @staticmethod
    def get_formatted_created_at(obj) -> str:
        return format_created_at(obj.created_at)

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']

class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
    )
    attachments = PostAttachmentSerializer(read_only=True, many=True)
    formatted_created_at = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        source='tags',
        read_only=True,
    )
    title = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'content', 'author', 'category', 'category_id', 'comments',
            'tag_ids', 'created_at', 'updated_at',  'view_count', 'is_pinned',
            'attachments', 'formatted_created_at', 'comments_count', 'is_able', 'fake_name',
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

class PostEditRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['title', 'content']


