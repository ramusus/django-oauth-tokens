from django.conf import settings
from tyoi.oauth2 import AccessTokenRequest, AccessTokenRequestError, AccessTokenResponseError
from tyoi.oauth2.grants import AuthorizationCode, ClientCredentials
from tyoi.oauth2.authenticators import ClientPassword
from urlparse import urlparse
from models import AccessToken
import requests
import logging

log = logging.getLogger('oauth_tokens')

class BaseAccessToken(object):

    def __init__(self):
        self.client_id = self.get_setting('client_id')
        self.client_secret = self.get_setting('client_secret')
        self.scope = self.get_setting('scope')
        self.username = self.get_setting('username')
        self.password = self.get_setting('password')

        # TODO: remove stupid urls
        self.redirect_uri = 'http://ram-laptop.ru/auth/'
        self.return_to = 'http://ram-laptop.ru/auth/'

    def get_setting(self, key):
        return getattr(settings, 'OAUTH_TOKENS_%s_%s' % (self.provider.upper(), key.upper()))

    def parse_auth_form(self, page_content):
        '''
        Parse page with auth form and return tuple with (method, form action, form submit parameters)
        '''
        raise NotImplementedError()

    def parse_permissions_form(self, page_content):
        '''
        Parse page with permissions form and return tuple with (method, form action, form submit parameters)
        '''
        raise NotImplementedError()

    def get(self):
        '''
        Get new token from provider
        '''
        auth_uri = AuthorizationCode.build_auth_uri(
            endpoint = self.authenticate_url,
            client_id = self.client_id,
            scope = self.scope,
            redirect_uri = self.redirect_uri
        )
        log.debug(auth_uri)

        response = requests.get(auth_uri)
        log.debug(response.__dict__)
        method, action, data = self.parse_auth_form(response.content)

        # submit auth form data
        response = requests.post(action, data)
        log.debug(response.__dict__)
        log.debug(response.headers['location'])

        response = requests.get(response.headers['location'], cookies=response.cookies)
        log.debug(response.__dict__)
        params = dict([part.split('=') for part in urlparse(response.url)[4].split('&')])
        if 'code' not in params:
            # it's neccesary additionally to approve requested permissions
            method, approve_url, data = self.parse_permissions_form(response.content)
            log.debug(approve_url)
            response = requests.get(approve_url, cookies=response.cookies)
            log.debug(response.__dict__)
            params = dict([part.split('=') for part in urlparse(response.url)[4].split('&')])
            if 'code' not in params:
                raise Exception("Vkontakte OAuth response didn't return code parameter")

        code = params['code']

        grant = AuthorizationCode(code, self.return_to)
#       grant = ClientCredentials(scope='32768')
        authenticator = ClientPassword(self.client_id, self.client_secret)
        oauth_request = AccessTokenRequest(authenticator, grant, self.access_token_url)

        try:
            token = oauth_request.send(self.response_decoder)
            return token
        except AccessTokenRequestError, ex:
            log.error('Invalid response from oauth provider [code=%s]' % ex.error_code)
            log.error(u'[start]%s[end]' % (ex.error_description or ex.error_code_description))
            return False
        except AccessTokenResponseError, ex:
            log.error('Invalid response from oauth provider: %s' % ex.message)
            return False
        except Exception, e:
            log.error('Error: %s' % e)
            return False

        return False