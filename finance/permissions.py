from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwner(BasePermission):
    """
    Object-level permission to only allow owners of an object to view/edit it.
    Assumes the model instance has a `user` attribute.
    """
    def has_object_permission(self, request, view, obj):
        return getattr(obj, "user_id", None) == getattr(request.user, "id", None)

class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS
