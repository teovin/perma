import logging
import re

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.template import Context, RequestContext, engines
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .models import Registrar, LinkUser
from .utils import tz_datetime

logger = logging.getLogger(__name__)


def render_email(template, context, request=None):
    # load the django template engine directly, so that we can
    # pass in a Context/RequestContext object with autocomplete=False
    # https://docs.djangoproject.com/en/1.11/topics/templates/#django.template.loader.engines
    #
    # (though render and render_to_string take a "context" kwarg of type dict,
    #  that dict cannot be used to configure autoescape, but only to pass keys/values to the template)
    engine = engines['django'].engine
    if request:
        ctx = RequestContext(request, context, autoescape=False)
    else:
        ctx = Context(context, autoescape=False)
    return engine.get_template(template).render(ctx)


###
### Send email
###

def send_user_email(to_address, template, context):
    email_text = render_email(template, context)
    title, email_text = email_text.split("\n\n", 1)
    title = title.split("TITLE: ")[-1]

    message = EmailMessage(
        title,
        email_text,
        settings.DEFAULT_FROM_EMAIL,
        [to_address]
    )
    return message.send(fail_silently=False)

# def send_mass_user_email(template, recipients):
    # '''
    #     Opens a single connection to the mail server and sends many emails.
    #     Pass in recipients as a list of tuples (email, context):
    #     [('recipient@example.com', {'first_name': 'Joe', 'last_name': 'Yacoboski' }), (), ...]
    # '''
    # to_send = []
    # for recipient in recipients:
    #     to_address, context = recipient
    #     email_text = render_email(template, context)
    #     title, email_text = email_text.split("\n\n", 1)
    #     title = title.split("TITLE: ")[-1]
    #     to_send.append(( title,
    #                      email_text,
    #                      settings.DEFAULT_FROM_EMAIL,
    #                      [to_address]))

    # success_count = send_mass_mail(tuple(to_send), fail_silently=False)
    # return success_count

def send_admin_email(title, from_address, request, template="email/default.txt", context={}):
    """
        Send a message on behalf of a user to the admins.
        Use reply-to for the user address so we can use email services that require authenticated from addresses.
    """
    message = EmailMessage(
        title,
        render_email(template, context, request),
        settings.DEFAULT_FROM_EMAIL,
        [settings.DEFAULT_FROM_EMAIL],
        headers={'Reply-To': from_address}
    )
    return message.send(fail_silently=False)


def send_self_email(title, request, template="email/default.txt", context={}, devs_only=True):
    """
        Send a message to ourselves. By default, sends only to settings.ADMINS.
        To contact the main Perma email address, set devs_only=False
    """
    if devs_only:
        message = EmailMessage(
            title,
            render_email(template, context, request),
            settings.DEFAULT_FROM_EMAIL,
            [admin[1] for admin in settings.ADMINS]
        )
    else:
        # Use a special reply-to address to avoid Freshdesk's filters: a ticket will be opened.
        message = EmailMessage(
            title,
            render_email(template, context, request),
            settings.DEFAULT_FROM_EMAIL,
            [settings.DEFAULT_FROM_EMAIL],
            headers={'Reply-To': settings.DEFAULT_REPLYTO_EMAIL}
        )
    return message.send(fail_silently=False)


def send_user_email_copy_admins(
    title: str,
    from_address: str,
    to_addresses: list[str],
    request: HttpRequest,
    template: str = 'email/default.txt',
    context: dict | None = None,
):
    """Send a message to a user, CCing the sender and the Perma admins.

    This can be used to send a message from one user to another while
    copying the admins, or to send a message from Perma to a user while
    CCing a copy to the admins.

    Use reply_to for the user address so we can use email services that
    require authenticated from addresses.
    """
    # Handle cases where we want to email a user and CC ourselves
    cc_addresses = [settings.DEFAULT_FROM_EMAIL]
    if from_address != settings.DEFAULT_FROM_EMAIL:
        cc_addresses.append(from_address)
    context = context if context is not None else {}
    message = EmailMessage(
        subject=title,
        body=render_email(template, context, request),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=to_addresses,
        cc=cc_addresses,
        reply_to=[from_address],
    )
    return message.send(fail_silently=False)

###
### Collect user data, bundled for emails ###
###

def registrar_users(registrars=None):
    '''
        Returns all active registrar users plus assorted metadata as
        a list of dicts.
    '''
    users = []
    if registrars is None:
        registrars = Registrar.objects.all()
    for registrar in registrars:
        registrar_users = LinkUser.objects.filter(registrar = registrar.pk,
                                                  is_active = True,
                                                  is_confirmed = True)
        for user in registrar_users:
            users.append({
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "raw_email": user.raw_email,
            })
    return users


def registrar_users_plus_stats(registrars=None, year=None):
    '''
        Returns all active registrar users plus assorted metadata as
        a list of dicts. By default, uses stats from current
        calendar year.
    '''
    users = []
    if year is None:
        year = timezone.now().year
    start_time = tz_datetime(year, 1, 1)
    end_time = tz_datetime(year + 1, 1, 1)
    if registrars is None:
        registrars = Registrar.objects.all()
    for registrar in registrars:
        registrar_users = LinkUser.objects.filter(registrar = registrar.pk,
                                                  is_active = True,
                                                  is_confirmed = True)
        for user in registrar_users:
            users.append({ "first_name": user.first_name,
                           "last_name": user.last_name,
                           "email": user.email,
                           "registrar_id": registrar.id,
                           "registrar_email": registrar.email,
                           "registrar_name": registrar.name,
                           "total_links": registrar.link_count,
                           "year_links": registrar.link_count_in_time_period(start_time, end_time),
                           "most_active_org": registrar.most_active_org_in_time_period(start_time, end_time),
                           "registrar_users": registrar_users })
    return users


###
### Signup and activation helpers
###

def get_activation_email_context(
    user: LinkUser,
    *,
    request: HttpRequest | None = None,
    host: str | None = None,
) -> dict[str, str | int]:
    """
    Build activation_route and activation_expires for new-user email templates.

    Uses Django's password_reset_confirm flow. Pass request for sync sends, or host
    (e.g. "https://perma.cc") for async/Celery sends where no request is available.
    """
    path = reverse(
        'password_reset_confirm',
        args=[
            urlsafe_base64_encode(force_bytes(user.pk)),
            default_token_generator.make_token(user),
        ],
    )
    if request is not None:
        activation_route = request.build_absolute_uri(path)
    elif host is not None:
        activation_route = f'{host}{path}'
    else:
        raise ValueError('request or host is required')
    return {
        'activation_route': activation_route,
        'activation_expires': settings.PASSWORD_RESET_TIMEOUT,
    }


SIGNUP_NEW_USER_TEMPLATE = 'email/new_user.txt'
STAFF_INVITED_TEMPLATE = 'email/new_user_added_by_other.txt'
STAFF_INVITED_CUSTOM_TEMPLATE = 'email/new_user_added_by_other_custom.txt'


def suggest_registrars(user: LinkUser, limit: int = 5) -> QuerySet[Registrar]:
    """Suggest registrars whose website domain matches the user's email domain."""
    _, email_domain = user.email.split('@')
    base_domain = '.'.join(email_domain.rsplit('.', 2)[-2:])
    pattern = f'^https?://([a-zA-Z0-9\\-\\.]+\\.)?{re.escape(base_domain)}(/.*)?$'
    return (
        Registrar.objects.filter(status='approved')
        .filter(website__iregex=pattern)
        .order_by('-link_count', 'name')[:limit]
    )


def send_signup_new_user_email(
    request: HttpRequest,
    user: LinkUser,
    *,
    template: str = SIGNUP_NEW_USER_TEMPLATE,
    context: dict | None = None,
) -> None:
    """Send activation email for self-signup or resend activation."""
    # Shallow-copy so updates (activation fields, suggested_registrars) do not mutate the caller's dict.
    context = dict(context) if context is not None else {}
    context.update(get_activation_email_context(user, request=request))
    context['request'] = request
    if template == SIGNUP_NEW_USER_TEMPLATE:
        context['suggested_registrars'] = suggest_registrars(user)
    send_user_email(user.raw_email, template, context)


def send_staff_invited_new_user_email(
    user: LinkUser,
    *,
    registrar_id: int | None = None,
    context: dict | None = None,
    request: HttpRequest | None = None,
    host: str | None = None,
) -> None:
    """Send activation email when staff add a new user.

    Pass `registrar_id` when the invite is tied to a registrar (org, registrar user,
    sponsorship, bulk org add) so CUSTOM_EMAILS_FOR_REGISTRAR can be applied. Use
    ``None`` when there is no registrar (admin or individual user invites, or an
    organization with no sponsoring registrar); custom templates are skipped.
    """
    # Shallow-copy so updates (activation fields, registrar custom config) do not mutate the caller's dict.
    context = dict(context) if context is not None else {}
    context.update(get_activation_email_context(user, request=request, host=host))
    template = STAFF_INVITED_TEMPLATE

    if registrar_id is not None:
        custom_config = settings.CUSTOM_EMAILS_FOR_REGISTRAR.get(registrar_id)
        if custom_config:
            template = custom_config.get('template_file', STAFF_INVITED_CUSTOM_TEMPLATE)
            context.update(
                {k: v for k, v in custom_config.items() if k != 'template_file'}
            )

    send_user_email(user.raw_email, template, context)
