from rest_framework.authentication import TokenAuthentication as DRFTokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from perma.models import ApiKey


class TokenAuthentication(DRFTokenAuthentication):
    """
        Override default TokenAuth to use our api key table and custom keyword in the Authorization header.
    """
    keyword = 'ApiKey'
    model = ApiKey

    def authenticate(self, request):
        """
            Try getting api_key from get/post param before using Authorization header.
        """
        api_key = request.POST.get('api_key') or request.query_params.get('api_key')
        if api_key:
            return self.authenticate_credentials(api_key)
        return super(TokenAuthentication, self).authenticate(request)

    def authenticate_credentials(self, key):
        """
            API key authentication is disabled for admin users. They can still
            use the API via session auth (e.g. the dashboard), but a key must
            not authenticate them. Cookie/session requests never reach this
            method, so the dashboard is unaffected.
        """
        user, api_key = super(TokenAuthentication, self).authenticate_credentials(key)
        if user.is_staff:
            raise AuthenticationFailed('API key authentication is disabled for admin users.')
        return user, api_key