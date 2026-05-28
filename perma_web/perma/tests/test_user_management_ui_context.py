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

    assert flags["show_upgrade_interest_note"] is True
    assert flags["show_full_manage_title"] is True
    assert flags["show_org_manage_title"] is False
    assert flags["show_manage_sidebar"] is True
    assert flags["show_admin_registrar_nav"] is True
    assert flags["show_individual_users_nav"] is True


@pytest.mark.django_db
def test_registrar_base_flags(make_manage_request, registrar_user):
    flags = build_user_management_ui(make_manage_request(registrar_user))

    assert flags["show_upgrade_interest_note"] is False
    assert flags["show_full_manage_title"] is True
    assert flags["show_admin_registrar_nav"] is False
    assert flags["show_registrar_sponsored_nav"] is True
    assert flags["can_use_sponsor_terminology"] is True
    assert flags["can_edit_remove_as_registrar"] is True


@pytest.mark.django_db
def test_org_user_base_flags(make_manage_request, org_user):
    flags = build_user_management_ui(make_manage_request(org_user))

    assert flags["show_org_manage_title"] is True
    assert flags["show_full_manage_title"] is False
    assert flags["show_manage_sidebar"] is True
    assert flags["show_admin_registrar_nav"] is False
    assert flags["show_registrar_sponsored_nav"] is False


@pytest.mark.django_db
def test_manage_orgs_screen_flags(make_manage_request, admin_user, registrar_user, org_user):
    staff_flags = build_user_management_ui(make_manage_request(admin_user), screen="manage_orgs")
    assert staff_flags["can_add_organization"] is True
    assert staff_flags["show_registrar_org_filter"] is True

    registrar_flags = build_user_management_ui(make_manage_request(registrar_user), screen="manage_orgs")
    assert registrar_flags["can_add_organization"] is True
    assert registrar_flags["show_registrar_org_filter"] is False

    org_flags = build_user_management_ui(make_manage_request(org_user), screen="manage_orgs")
    assert org_flags["can_add_organization"] is False
    assert org_flags["show_registrar_org_filter"] is False


@pytest.mark.django_db
def test_user_list_group_name_flags(make_manage_request, admin_user, registrar_user):
    staff_user_list = build_user_management_ui(make_manage_request(admin_user), group_name="user")
    assert staff_user_list["group_name"] == "user"
    assert staff_user_list["show_four_column_stats"] is True
    assert staff_user_list["show_deactivated_count"] is True
    assert staff_user_list["show_upgrade_interest_filter"] is True
    assert staff_user_list["can_view_sponsored_user_links"] is False

    staff_sponsored_list = build_user_management_ui(
        make_manage_request(admin_user), group_name="sponsored_user"
    )
    assert staff_sponsored_list["show_four_column_stats"] is False
    assert staff_sponsored_list["show_affiliation_filters"] is True
    assert staff_sponsored_list["can_view_sponsored_user_links"] is False

    registrar_sponsored_list = build_user_management_ui(
        make_manage_request(registrar_user), group_name="sponsored_user"
    )
    assert registrar_sponsored_list["can_view_sponsored_user_links"] is True
    assert registrar_sponsored_list["show_registrar_filter"] is False


@pytest.mark.django_db
def test_group_name_and_screen_are_mutually_exclusive_sections(make_manage_request, admin_user):
    """screen=manage_orgs should not also apply user-list keys."""
    flags = build_user_management_ui(make_manage_request(admin_user), screen="manage_orgs")
    assert "group_name" not in flags
    assert "show_four_column_stats" not in flags

    flags = build_user_management_ui(make_manage_request(admin_user), group_name="user")
    assert "can_add_organization" not in flags
