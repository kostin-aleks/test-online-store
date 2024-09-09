"""

"""

from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.exceptions import NotAuthenticated, PermissionDenied


class IsSuperUser(BasePermission):
    """Allows access only to superusers."""

    def has_permission(self, request, view):
        """permission logic"""
        return bool(request.user.is_authenticated and request.user.is_superuser)


class IsAdminUserOrReadOnly(BasePermission):
    """
    Allows access only to admin users, or is a read-only request.
    """

    def has_permission(self, request, view):
        """permission logic"""
        return bool(
            # Read permissions are allowed to any request,
            # so we'll always allow GET, HEAD or OPTIONS requests.
            request.method in SAFE_METHODS
            or request.user and request.user.is_staff
        )


class IsClientUser(BasePermission):
    """Allows access only to client users."""

    def has_permission(self, request, view):
        """permission logic"""
        if request.user.is_anonymous:
            raise NotAuthenticated
        return True


class IsManager(BasePermission):
    """Allows access only to manager users."""

    def has_permission(self, request, view):
        """permission logic"""
        if request.user.is_anonymous:
            raise NotAuthenticated
        if request.user.userprofile and \
           not request.user.userprofile.has_manager_permission():
            raise PermissionDenied

        return True


class IsManagerOrReadOnly(BasePermission):
    """
    Allows access only to managers, or is a read-only request.
    """

    def has_permission(self, request, view):
        """permission logic"""
        return bool(
            # Read permissions are allowed to any request,
            # so we'll always allow GET, HEAD or OPTIONS requests.
            request.method in SAFE_METHODS
            or \
            (request.user.is_authenticated and request.user.userprofile \
             and request.user.userprofile.has_manager_permission())
        )
