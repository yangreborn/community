from rest_framework import permissions

class IsOwnerAuditorOrApproved(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        # 允许管理员查看所有内容
        if request.user.groups.filter(name='auditors').exists():
            return True
        # 允许作者查看自己的内容
        if hasattr(obj, 'author') and obj.author == request.user:
            return True
        # 允许查看已审核通过的内容
        return obj.is_create_approved

class IsOwnerOrAuditor(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_superuser:
            return True
        if request.user.is_authenticated:
            if request.user.groups.filter(name='auditors').exists():
                return True
            return obj.author == request.user
        return False
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated

class IsAuditor(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        return request.user.groups.filter(name='auditors').exists()
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        return request.user.groups.filter(name='auditors').exists()