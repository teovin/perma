import pytest
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.test import RequestFactory
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from perma.email import get_activation_email_context, registrar_users_plus_stats, send_user_email_copy_admins
from perma.models import LinkUser, Organization, Registrar


def test_get_activation_email_context_with_request(link_user_factory):
    user = link_user_factory()
    request = RequestFactory().get('/')
    context = get_activation_email_context(user, request=request)
    assert context['activation_expires'] == settings.PASSWORD_RESET_TIMEOUT
    expected_path = reverse(
        'password_reset_confirm',
        args=[
            urlsafe_base64_encode(force_bytes(user.pk)),
            default_token_generator.make_token(user),
        ],
    )
    assert context['activation_route'] == request.build_absolute_uri(expected_path)


def test_get_activation_email_context_with_host(link_user_factory):
    user = link_user_factory()
    context = get_activation_email_context(user, host='https://perma.cc')
    assert context['activation_expires'] == settings.PASSWORD_RESET_TIMEOUT
    expected_path = reverse(
        'password_reset_confirm',
        args=[
            urlsafe_base64_encode(force_bytes(user.pk)),
            default_token_generator.make_token(user),
        ],
    )
    assert context['activation_route'] == f'https://perma.cc{expected_path}'


def test_get_activation_email_context_requires_request_or_host(link_user_factory):
    with pytest.raises(ValueError, match='request or host'):
        get_activation_email_context(link_user_factory())


def test_send_user_email_copy_admins(mailoutbox):
    send_user_email_copy_admins(
        "title",
        "from@example.com",
        ["to@example.com"],
        HttpRequest(),
        "email/default.txt",
        {"message": "test message"}
    )
    assert len(mailoutbox) == 1
    message = mailoutbox[0]
    assert message.from_email == settings.DEFAULT_FROM_EMAIL
    assert message.cc == [settings.DEFAULT_FROM_EMAIL, "from@example.com"]
    assert message.to == ["to@example.com"]
    assert message.reply_to == ["from@example.com"]


def test_registrar_users_plus_stats_specific_registrars(db):
    '''
        Returns data in the expected format.
    '''
    r_list = registrar_users_plus_stats(registrars=Registrar.objects.filter(email='library@university.edu'))
    assert isinstance(r_list, list)
    assert len(r_list) == 1
    assert r_list[0]['registrar_email'] == 'library@university.edu'


def test_registrar_users_plus_stats(db):
    '''
        Returns data in the expected format.
    '''
    r_list = registrar_users_plus_stats()
    assert isinstance(r_list, list)
    assert len(r_list) > 0
    for user in r_list:
        assert isinstance(user, dict)
        expected_keys = [ 'email',
                          'first_name',
                          'last_name',
                          'most_active_org',
                          'registrar_email',
                          'registrar_id',
                          'registrar_name',
                          'registrar_users',
                          'total_links',
                          'year_links' ]
        assert sorted(user.keys()) == expected_keys
        for key in ['email', 'first_name', 'last_name', 'registrar_email', 'registrar_name']:
            assert isinstance(user[key], str)
            assert user[key]
        perma_user = LinkUser.objects.get(email=user['email'])
        assert perma_user.registrar
        assert perma_user.is_active
        assert perma_user.is_confirmed
        assert isinstance(user['total_links'], int)
        assert isinstance(user['year_links'], int)
        assert isinstance(user['registrar_id'], int)
        assert isinstance(user['most_active_org'], (Organization, type(None)))
        assert isinstance(user['registrar_users'], QuerySet)
        assert len(user['registrar_users']) >= 1
        for user in user['registrar_users']:
            assert isinstance(user, LinkUser)
