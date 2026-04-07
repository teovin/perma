"""
Semantic UI flags around permissions for user-management templates.

Views that need screen-specific keys should set context['user_management_perms']
by calling build_user_management_perms() with screen=..., which replaces the user_management_perms dict

screen:
  None — base flags.
  "manage_orgs" — organization list page extras.
  Any user-list group slug (e.g. "user", "organization_user") — same as former group_name.
"""

from typing import Any
from django.http import HttpRequest
from perma.permissions.user_management_access import (
    allow_staff,
    allow_registrar,
    allow_organization_user,
    allow_staff_or_registrar,
    allow_staff_registrar_or_org_user
)


def build_user_management_perms(
    request: HttpRequest,
    screen: str | None = None,
) -> dict[str, Any]:
    
    user = request.user
    if not user.is_authenticated:
        return {}

    ui_flags = {
        "is_staff": allow_staff(user),
        "can_show_user_management_title": allow_staff_or_registrar(user),
        "can_show_organization_only_management_title": allow_organization_user(user) and not allow_staff_or_registrar(user),
        "can_show_user_management_sidebar": allow_staff_registrar_or_org_user(user),
        "can_show_admin_users_and_registrars_nav": allow_staff(user),
        "can_show_registrar_users_and_sponsored_users_nav": allow_staff_or_registrar(user),
        "can_show_regular_users_nav": allow_staff(user),
        "can_show_select_button_for_registrar_user": allow_staff(user),
        "can_show_registrar_admin_console_link": allow_staff(user),
        "can_link_to_registrar_in_registrar_list": allow_staff(user),
        "can_delete_or_deactivate_user": allow_staff(user),
        "can_show_edit_remove_buttons_to_staff_users": allow_staff(user),
        "can_show_edit_remove_buttons_to_registrar_users": allow_registrar(user),
        "can_reactivate_user": allow_staff(user),
        "can_edit_sponsorship_or_delete_for_sponsored_users": allow_staff(user),
        "can_view_warning_messages_for_adding_user_to_registrar": allow_staff(user),
        "can_use_sponsor_user_terminology": allow_registrar(user),
        "can_see_modified_button_label_for_edit_sponsorship": allow_staff(user)
    }


    if screen == "manage_orgs":
        ui_flags.update(
            {
                "can_add_organization": allow_staff_or_registrar(user),
                "can_show_organization_registrar_filter": allow_staff(user),
                "can_show_organization_registrar_affiliation": allow_staff(user),
                "can_show_organization_admin_console_link": allow_staff(user),
            }
        )

    elif screen is not None:
        group_name = screen # screen is the same as group_name for user-list pages
        ends_with_user = group_name.endswith("user")
        ui_flags.update(
            {
                "group_name": group_name,
                "can_show_user_stats": allow_staff(user) and group_name == "user",
                "can_show_deactivated_user_stat": allow_staff(user) and group_name == "user",
                "can_show_upgrade_interest_filter": allow_staff(user) and group_name == "user",
                "can_show_deactivated_status_filter": allow_staff(user) and ends_with_user,
                "can_show_org_and_sponsorship_filters": allow_staff_or_registrar(user) and group_name in ("organization_user", "sponsored_user"),
                "can_show_registrar_filter_dropdown": allow_staff(user) and group_name not in ("user", "admin_user"),
                "can_show_registrar_affiliation_for_registrar_user": allow_staff(user) and group_name == "registrar_user",
                "can_view_registrar_links_copy": allow_staff(user),
                "can_show_user_admin_console_link": allow_staff(user),
                "can_show_view_links_button_for_registrar": group_name == "sponsored_user" and not allow_staff(user)
            }
        )

    return ui_flags


def user_management_perms(request: HttpRequest) -> dict[str, Any]:
    return {"user_management_perms": build_user_management_perms(request)}
