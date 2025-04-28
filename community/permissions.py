from rest_framework import permissions

class IsOwnerAdminOrApproved(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # 允许管理员查看所有内容
        if request.user.is_staff:
            return True
        # 允许作者查看自己的内容
        if hasattr(obj, 'author') and obj.author == request.user:
            return True
        # 允许查看已审核通过的内容
        return obj.approved

class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_authenticated:
            if request.user.is_admin():
                return True
            return obj.author == request.user
        return False

class IsAdminUser(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff