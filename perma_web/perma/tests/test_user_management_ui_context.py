from django.contrib.auth.models import AnonymousUser
from django.test.client import RequestFactory

import pytest

from perma.views.user_management.ui_context import build_user_management_ui


@pytest.fixture
def make_manage_request():
    factory = RequestFactory()

    def _make(user=None):
        request = factory.get("/manage/")
        request.user = AnonymousUser() if user is None else user
        return request

    return _make


@pytest.mark.django_db
def test_unauthenticated_user_returns_empty_flags(make_manage_request):
    assert build_user_management_ui(make_manage_request()) == {}


@pytest.mark.django_db
def test_request_without_user_attribute_returns_empty_flags():
    request = RequestFactory().get("/manage/")
    assert build_user_management_ui(request) == {}


@pytest.mark.django_db
def test_staff_base_flags(make_manage_request, admin_user):
    flags = build_user_management_ui(make_manage_request(admin_user))

    assert flags["is_staff"] is True
    assert flags["can_show_user_management_title"] is True
    assert flags["can_show_organization_only_management_title"] is False
    assert flags["can_show_user_management_sidebar"] is True
    assert flags["can_show_admin_users_and_registrars_nav"] is True
    assert flags["can_show_regular_users_nav"] is True


@pytest.mark.django_db
def test_registrar_base_flags(make_manage_request, registrar_user):
    flags = build_user_management_ui(make_manage_request(registrar_user))

    assert flags["is_staff"] is False
    assert flags["can_show_user_management_title"] is True
    assert flags["can_show_admin_users_and_registrars_nav"] is False
    assert flags["can_show_registrar_users_and_sponsored_users_nav"] is True
    assert flags["can_use_sponsor_user_terminology"] is True
    assert flags["can_show_edit_remove_buttons_to_registrar_users"] is True


@pytest.mark.django_db
def test_org_user_base_flags(make_manage_request, org_user):
    flags = build_user_management_ui(make_manage_request(org_user))

    assert flags["can_show_organization_only_management_title"] is True
    assert flags["can_show_user_management_title"] is False
    assert flags["can_show_user_management_sidebar"] is True
    assert flags["can_show_admin_users_and_registrars_nav"] is False
    assert flags["can_show_registrar_users_and_sponsored_users_nav"] is False


@pytest.mark.django_db
def test_manage_orgs_screen_flags(make_manage_request, admin_user, registrar_user, org_user):
    staff_flags = build_user_management_ui(make_manage_request(admin_user), screen="manage_orgs")
    assert staff_flags["can_add_organization"] is True
    assert staff_flags["can_show_organization_registrar_filter"] is True

    registrar_flags = build_user_management_ui(make_manage_request(registrar_user), screen="manage_orgs")
    assert registrar_flags["can_add_organization"] is True
    assert registrar_flags["can_show_organization_registrar_filter"] is False

    org_flags = build_user_management_ui(make_manage_request(org_user), screen="manage_orgs")
    assert org_flags["can_add_organization"] is False
    assert org_flags["can_show_organization_registrar_filter"] is False


@pytest.mark.django_db
def test_user_list_group_name_flags(make_manage_request, admin_user, registrar_user):
    staff_user_list = build_user_management_ui(make_manage_request(admin_user), group_name="user")
    assert staff_user_list["group_name"] == "user"
    assert staff_user_list["can_show_user_stats"] is True
    assert staff_user_list["can_show_deactivated_user_stat"] is True
    assert staff_user_list["can_show_upgrade_interest_filter"] is True
    assert staff_user_list["can_show_view_links_button_for_registrar"] is False

    staff_sponsored_list = build_user_management_ui(
        make_manage_request(admin_user), group_name="sponsored_user"
    )
    assert staff_sponsored_list["can_show_user_stats"] is False
    assert staff_sponsored_list["can_show_org_and_sponsorship_filters"] is True
    assert staff_sponsored_list["can_show_view_links_button_for_registrar"] is False

    registrar_sponsored_list = build_user_management_ui(
        make_manage_request(registrar_user), group_name="sponsored_user"
    )
    assert registrar_sponsored_list["can_show_view_links_button_for_registrar"] is True
    assert registrar_sponsored_list["can_show_registrar_filter_dropdown"] is False


@pytest.mark.django_db
def test_group_name_and_screen_are_mutually_exclusive_sections(make_manage_request, admin_user):
    """screen=manage_orgs should not also apply user-list keys."""
    flags = build_user_management_ui(make_manage_request(admin_user), screen="manage_orgs")
    assert "group_name" not in flags
    assert "can_show_user_stats" not in flags

    flags = build_user_management_ui(make_manage_request(admin_user), group_name="user")
    assert "can_add_organization" not in flags
