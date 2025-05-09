from rest_framework import serializers
from .models import Category, Demand, Comment, DemandStatusChange
from community.utils import format_created_at
from account.serializers import UserSerializer

class CategorySerializer(serializers.ModelSerializer):
    count = serializers.SerializerMethodField(help_text='分类下帖子数')
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'count', 'parent_id']
        ref_name = 'DemandCategorySerializer'

    @staticmethod
    def get_count(obj):
        return len(obj.posts.all())

class CommentSerializer(serializers.ModelSerializer):
    formatted_created_at = serializers.SerializerMethodField(help_text='格式化创建时间')
    class Meta:
        model = Comment
        fields = ['id', 'author', 'demand', 'content', 'created_at', 'formatted_created_at', 'parent_comment']
        read_only_fields = ('created_at',)
        ref_name = 'DemandCommentSerializer'

    @staticmethod
    def get_formatted_created_at(obj) -> str:
        return format_created_at(obj.created_at)

class DemandSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
    )
    formatted_created_at = serializers.SerializerMethodField(help_text='格式化创建时间')
    comments = serializers.SerializerMethodField()
    class Meta:
        model = Demand
        fields = [
            'id', 'title', 'description', 'author', 'category', 'category_id', 'comments',
            'created_at', 'updated_at', 'formatted_created_at',  'is_able', 'status', 'status_display',
        ]
        read_only_fields = ('created_at', 'updated_at', 'author', 'is_able', )

    @staticmethod
    def get_formatted_created_at(obj) -> str:
        return format_created_at(obj.created_at)

    def get_comments(self, obj):
        comments = obj.comments.all()
        return CommentSerializer(comments, many=True, context=self.context).data


class StatusChangeSerializer(serializers.ModelSerializer):
    changed_by = serializers.StringRelatedField()

    class Meta:
        model = DemandStatusChange
        fields = ['from_status', 'to_status', 'changed_by', 'change_reason', 'changed_at']
        read_only_fields = fields