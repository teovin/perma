"""
Access conditions for user-management views (@user_passes_test_or_403).

Keep logic centralized here so authorization matches with
views.user_management.ui_context where the same user rules apply.
"""

from perma.models import LinkUser


def allow_staff(user: LinkUser) -> bool:
    return bool(user.is_staff)


def allow_registrar(user: LinkUser) -> bool:
    return bool(user.is_registrar_user())


def allow_organization_user(user: LinkUser) -> bool:
    return bool(user.is_organization_user)


def allow_staff_or_registrar(user: LinkUser) -> bool:
    return bool(user.is_staff or user.is_registrar_user())


def allow_staff_registrar_or_org_user(user: LinkUser) -> bool:
    return bool(user.is_staff or user.is_registrar_user() or user.is_organization_user)
