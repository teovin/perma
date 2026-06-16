from typing import Any

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from perma.views.user_management.ui_context import ManageOrgsScreen, build_user_management_ui


def add_user_management_ui(
    context: dict[str, Any],
    request: HttpRequest,
    *,
    group_name: str | None = None,
    screen: ManageOrgsScreen | None = None,
) -> dict[str, Any]:
    if group_name is None:
        group_name = context.get("group_name")
    context["user_management_perms"] = build_user_management_ui(
        request,
        group_name=group_name,
        screen=screen,
    )
    return context


def render_user_management(
    request: HttpRequest,
    template: str,
    context: dict[str, Any] | None = None,
    *,
    group_name: str | None = None,
    screen: ManageOrgsScreen | None = None,
) -> HttpResponse:
    context = add_user_management_ui(
        context or {},
        request,
        group_name=group_name,
        screen=screen,
    )
    return render(request, template, context)
