from rest_framework import serializers
from account.models import User
from .models import Category, Post, Comment, PostAttachment

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

    def get_count(self, obj):
        return len(obj.posts.all())

class PostAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostAttachment
        fields = ['id', 'file', 'upload_at']
        read_only_fields = ('upload_at',)

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'author', 'post', 'content', 'created_at',]
        read_only_fields = ('created_at',)

class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
    )
    comments = CommentSerializer(read_only=True, many=True)
    attachments = PostAttachmentSerializer(read_only=True, many=True)


    class Meta:
        model = Post
        fields = [
            'id', 'title', 'content', 'author', 'category', 'category_id', 'comments',
            'created_at', 'updated_at', 'is_pinned', 'view_count',  'attachments'
        ]
        read_only_fields = ('created_at', 'updated_at', 'author', 'view_count', )