"""Context processor shim; logic lives in perma.views.user_management.ui_context."""

from typing import Any

from django.http import HttpRequest

from perma.views.user_management.ui_context import build_user_management_ui


def user_management_perms(request: HttpRequest) -> dict[str, Any]:
    return {"user_management_perms": build_user_management_ui(request)}
