from django import template


register = template.Library()



@register.filter(name="is_staff_or_registrar")
def is_staff_or_registrar_filter(user):
    """Whether the user is a staff or registrar user."""
    return user.is_staff or user.is_registrar_user()


@register.simple_tag
def user_has_manage_sidebar(user):
    """Whether the manage dashboard shows the left hand side navigation."""
    return user.is_staff or user.is_registrar_user() or user.is_organization_user


@register.inclusion_tag("includes/manage_dashboard_nav.html")
def render_manage_dashboard_nav(request_user, current_page):
    """Creates manage dashboard nav items for the requesting user."""
    item_metadata = [
        {
            "url_name": "user_management_manage_admin_user",
            "label": "Admin users",
            "visible": request_user.is_staff,
            "page_key": "users_admin_users",
        },
        {
            "url_name": "user_management_manage_registrar",
            "label": "Registrars",
            "visible": request_user.is_staff,
            "page_key": "users_registrars",
        },
        {
            "url_name": "user_management_manage_registrar_user",
            "label": "Registrar users",
            "visible": request_user.is_staff or request_user.is_registrar_user(),
            "page_key": "users_registrar_users",
        },
        {
            "url_name": "user_management_manage_sponsored_user",
            "label": "Sponsored users",
            "visible": request_user.is_staff or request_user.is_registrar_user(),
            "page_key": "users_sponsored_users",
        },
        {
            "url_name": "user_management_manage_organization",
            "label": "Organizations",
            "visible": request_user.is_staff or request_user.is_registrar_user() or request_user.is_organization_user,
            "page_key": "users_orgs",
        },
        {
            "url_name": "user_management_manage_organization_user",
            "label": "Org users",
            "visible": request_user.is_staff or request_user.is_registrar_user() or request_user.is_organization_user,
            "page_key": "users_organization_users",
        },
        {
            "url_name": "user_management_manage_user",
            "label": "Users",
            "visible": request_user.is_staff,
            "page_key": "users_users",
        },
    ]

    nav_items = []
    
    for item in item_metadata:
        if item["visible"]:
            nav_items.append(
                {
                    "url_name": item["url_name"],
                    "label": item["label"],
                    "is_active": current_page == item["page_key"],
                }
            )

    return {"manage_nav_items": nav_items}

