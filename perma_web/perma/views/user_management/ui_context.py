"""
Boolean UI flags for user-management templates.

Views that need screen-specific keys should set context['user_management_perms']
by calling build_user_management_ui(), which replaces the context-processor dict.

Use group_name for user-list pages; use screen='manage_orgs' for the org list.
"""

from typing import Any, Literal

from django.http import HttpRequest

from perma.views.user_management.access import (
    allow_organization_user,
    allow_registrar,
    allow_staff,
    allow_staff_or_registrar,
    allow_staff_registrar_or_org_user,
)

ManageOrgsScreen = Literal["manage_orgs"]


def build_user_management_ui(
    request: HttpRequest,
    *,
    group_name: str | None = None,
    screen: ManageOrgsScreen | None = None,
) -> dict[str, Any]:
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {}

    ui_flags = {
        "show_full_manage_title": allow_staff_or_registrar(user),
        "show_org_manage_title": allow_organization_user(user) and not allow_staff_or_registrar(user),
        "show_manage_sidebar": allow_staff_registrar_or_org_user(user),
        "show_admin_registrar_nav": allow_staff(user),
        "show_registrar_sponsored_nav": allow_staff_or_registrar(user),
        "show_individual_users_nav": allow_staff(user),
        "can_select_pending_registrar": allow_staff(user),
        "can_link_registrar_admin": allow_staff(user),
        "can_link_registrar_in_heading": allow_staff(user),
        "can_delete_or_deactivate": allow_staff(user),
        "can_edit_remove_as_staff": allow_staff(user),
        "can_edit_remove_as_registrar": allow_registrar(user),
        "can_reactivate": allow_staff(user),
        "can_manage_unconfirmed_as_staff": allow_staff(user),
        "can_show_registrar_upgrade_warning": allow_staff(user),
        "can_use_sponsor_terminology": allow_registrar(user),
        "can_use_short_sponsorship_label": allow_staff(user),
        "show_upgrade_interest_note": allow_staff(user),
    }

    if screen == "manage_orgs":
        ui_flags.update(
            {
                "can_add_organization": allow_staff_or_registrar(user),
                "show_registrar_org_filter": allow_staff(user),
                "show_org_registrar_link": allow_staff(user),
                "can_link_org_admin": allow_staff(user),
            }
        )
    elif group_name is not None:
        ends_with_user = group_name.endswith("user")
        ui_flags.update(
            {
                "group_name": group_name,
                "show_four_column_stats": allow_staff(user) and group_name == "user",
                "show_deactivated_count": allow_staff(user) and group_name == "user",
                "show_upgrade_interest_filter": allow_staff(user) and group_name == "user",
                "show_deactivated_filter": allow_staff(user) and ends_with_user,
                "show_affiliation_filters": allow_staff_or_registrar(user) and group_name in ("organization_user", "sponsored_user"),
                "show_registrar_filter": allow_staff(user) and group_name not in ("user", "admin_user"),
                "show_listed_user_registrar": allow_staff(user) and group_name == "registrar_user",
                "can_link_sponsored_user_links": allow_staff(user),
                "can_link_user_admin": allow_staff(user),
                "can_view_sponsored_user_links": not allow_staff(user) and group_name == "sponsored_user",
            }
        )

    return ui_flags
