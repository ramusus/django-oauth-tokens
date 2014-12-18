from abc import ABCMeta, abstractproperty, abstractmethod
import logging
from urlparse import urlparse

from bs4 import BeautifulSoup
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import requests
from requests_oauthlib import OAuth1Session, OAuth2Session
from tyoi.oauth2 import AccessTokenRequest, AccessTokenRequestError, AccessTokenResponseError
from tyoi.oauth2.authenticators import ClientPassword
from tyoi.oauth2.grants import AuthorizationCode, ClientCredentials, RefreshToken

from .models import UserCredentials
log = logging.getLogger('oauth_tokens')


class OAuthError(Exception):
    pass


class UserAccessError(Exception):
    pass


class LoginPasswordError(Exception):
    pass


class AccountLocked(Exception):
    pass


class WrongRedirectUrl(Exception):
    pass


class BaseAccessToken(object):

    user = None
    cookies = None
    headers = {}

    def __init__(self, user=None, tag=None):
        '''
        TODO: remove  dependancy of self.user from this class
        '''
        self.user = user

        # we have a tag, no user and there is credentials in db -> find user with tag
        if not self.user and tag and UserCredentials.objects.count():
            try:
                self.user = UserCredentials.objects.filter(provider=self.provider, tags__name__in=[tag])[0]
            except KeyError:
                log.error("User with tag %s for provider %s does not exist" % (tag, self.provider))

        if getattr(self, 'redirect_uri', None):
            self.redirect_uri = self.get_setting('redirect_uri') or self.redirect_uri
            if getattr(self, 'return_to', None) is None:
                self.return_to = self.redirect_uri

        self.client_id = self.get_setting('client_id')
        self.client_secret = self.get_setting('client_secret')
        self.scope = self.get_setting('scope')
        self.username = self.get_setting('username')
        self.password = self.get_setting('password')

        required_settings = ['client_id', 'client_secret']
        if not self.user:
            required_settings += ['username', 'password']

        for required_setting in required_settings:
            if not getattr(self, required_setting):
                raise ImproperlyConfigured('Setting OAUTH_TOKENS_%s_%s should be specified in settings.py' % (
                    self.provider.upper(), required_setting.upper()))

    def get_setting(self, key):
        if self.user and key in ['username', 'password', 'additional']:
            return getattr(self.user, key)

        return getattr(settings, 'OAUTH_TOKENS_%s_%s' % (self.provider.upper(), key.upper()), None)

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

    def authorize(self):
        '''
        Authorize and set self.cookies for next requests and return response of last request
        DEPRECATED
        '''
        auth_uri = AuthorizationCode.build_auth_uri(
            endpoint=self.authenticate_url,
            client_id=self.client_id,
            scope=self.scope,
            redirect_uri=self.redirect_uri
        )
#        print auth_uri
        log.debug(auth_uri)

        response = requests.get(auth_uri, headers=self.headers, cookies=self.cookies)
        self.cookies = response.cookies
#        print response.url

        log.debug('Response form dict: %s' % response.__dict__)
        log.debug('Response form content: %s' % response.content)

        method, action, data = self.parse_auth_form(response.content)

        # submit auth form data
#         import ipdb
#         ipdb.set_trace()

#        print action
        response = requests.post(action, data, cookies=self.cookies, headers=self.headers)
        self.cookies = response.cookies
#        print response.url

        log.debug('Response auth dict: %s' % response.__dict__)
        log.debug('Response auth location: %s' % response.headers.get('location'))

        return response

    def authorized_request(self, method='get', **kwargs):
        '''
        DEPRECATED
        '''
        if method not in ['get', 'post']:
            raise ValueError('Only `get` and `post` are allowed methods')

        if not self.cookies:
            self.authorize()

        if self.cookies:
            return getattr(requests, method)(cookies=self.cookies, headers=kwargs.pop('headers', self.headers), **kwargs)
        else:
            raise ValueError('Cookies for authorized request are empty')

    def get_response_code(self, url):
        parsed_url = urlparse(url)
        if 'code' in parsed_url.query:
            part = parsed_url.query
        elif 'code' in parsed_url.fragment:
            part = parsed_url.fragment
        else:
            return None
        params = dict([part.split('=') for part in part.split('&')])
        return params['code'] if 'code' in params else None

    def refresh(self, refresh_token, scope):
        '''
        TODO: cover with tests
        '''
        grant = RefreshToken(refresh_token, scope)
        return self.send_grant_request(grant)

    def get(self):
        '''
        Get new token from provider
        TODO: migrate to requests_oauth
        '''
        response = self.authorize()

        if response.status_code == 302:
            print 'Redirect to: %s' % response.headers['location']
            response = self.authorized_request(url=response.headers['location'])

            log.debug('Response redirect dict: %s' % response.__dict__)
            log.debug('Response redirect content: %s' % response.content)

        code = self.get_response_code(response.url)
        if not code:
            # it's neccesary additionally to approve requested permissions
            method, approve_url, data = self.parse_permissions_form(response.content)
#            approve_url = 'https://oauth.vkontakte.ru/grant_access?hash=a6c75e8c325807e0e5&client_id=2735668&settings=32768&redirect_uri=http%3A%2F%2Fads.movister.ru%2F&response_type=code&state=&token_type=0'
            kwargs = {}
            if method == 'post':
                kwargs['data'] = data

            log.debug('Grant url: %s' % approve_url)

            response = requests.request(
                method, url=approve_url, cookies=response.cookies, headers=self.headers, **kwargs)

            log.debug('Response token dict: %s' % response.__dict__)
            log.debug('Response token content: %s' % response.content)

            code = self.get_response_code(response.url)
            if not code:
                raise Exception("OAuth response didn't return code parameter")

        log.debug('Code: %s' % code)

        grant = AuthorizationCode(code, self.return_to)
        return self.send_grant_request(grant)

    def send_grant_request(self, grant):
        '''
        DEPRECATED: migrate to requests_oauth
        '''
        authenticator = ClientPassword(self.client_id, self.client_secret)
        oauth_request = AccessTokenRequest(authenticator, grant, self.access_token_url)
#        print oauth_request.__dict__

        try:
            token = oauth_request.send(self.response_decoder)
            token.scope = ','.join(self.scope)
            return token
        except AccessTokenRequestError, ex:
            log.error('Invalid response from oauth provider [code=%s]' % ex.error_code)
            log.error(u'[start]%s[end]' % (ex.error_description or ex.error_code_description))
            raise
        except AccessTokenResponseError, ex:
            log.error('Invalid response from oauth provider: %s' % ex.message)
            raise
        except Exception, e:
            log.error('Error: %s' % e)
            raise


class SettingsMixin:

    def get_setting(self, key):
        return getattr(settings, 'OAUTH_TOKENS_%s_%s' % (self.provider.upper(), key.upper()), None)


class AccessTokenBase(object, SettingsMixin):

    __metaclass__ = ABCMeta

    def __init__(self, **kwargs):

        if self.type not in ['oauth1', 'oauth2']:
            raise ImproperlyConfigured("Property type should be equal 'oauth1' or 'oauth2'")

        if getattr(self, 'redirect_uri', None):
            self.redirect_uri = self.get_setting('redirect_uri') or self.redirect_uri
            if getattr(self, 'return_to', None) is None:
                self.return_to = self.redirect_uri

        self.client_id = self.get_setting('client_id')
        self.client_secret = self.get_setting('client_secret')
        self.scope = self.get_setting('scope')

        self.set_auth_request(**kwargs)

    def set_auth_request(self, **kwargs):
        self.auth_request = self.auth_request_class(**kwargs)

    def get(self):
        if self.type == 'oauth1':
            return self.oauth1_get()
        elif self.type == 'oauth2':
            return self.oauth2_get()

    def refresh(self, token):
        if self.type == 'oauth2':
            return self.oauth2_refresh(token)

    def oauth1_get(self):
        '''
        Get and return access_token from provider using OAuth1 workflow
        Based on docs http://requests-oauthlib.readthedocs.org/en/latest/oauth1_workflow.html
        '''
        self.oauth = OAuth1Session(self.client_id, client_secret=self.client_secret)
        fetch_response = self.oauth.fetch_request_token(self.request_token_url)
        resource_owner_key = fetch_response.get('oauth_token')
        resource_owner_secret = fetch_response.get('oauth_token_secret')

        # here always return pin, istead of oauth_verifier parameter
        verifier = self.user_authorization()

        self.oauth = OAuth1Session(self.client_id,
                                   client_secret=self.client_secret,
                                   resource_owner_key=resource_owner_key,
                                   resource_owner_secret=resource_owner_secret,
                                   verifier=verifier)
        oauth_tokens = self.oauth.fetch_access_token(self.access_token_url)
        resource_owner_key = oauth_tokens.get('oauth_token')
        resource_owner_secret = oauth_tokens.get('oauth_token_secret')

        return self.delimeter.join([resource_owner_key, resource_owner_secret])

    def oauth2_get(self):
        '''
        Get and return access_token from provider using OAuth2 workflow
        Based on docs http://requests-oauthlib.readthedocs.org/en/latest/oauth2_workflow.html
        '''
        self.oauth = OAuth2Session(self.client_id, redirect_uri=self.redirect_uri, scope=self.scope)

        authorization_response_url = self.user_authorization()
        # hack preventing to oauthlib comparing scope returned by response with initial
        # servers never returns scope parameter with token
        self.oauth.scope = None
        token = self.oauth.fetch_token(self.access_token_url,
                                       authorization_response=authorization_response_url,
                                       client_secret=self.client_secret)
        # set scope manually
        token['scope'] = self.scope
        return token

    def oauth2_refresh(self, token):
        self.oauth = OAuth2Session(self.client_id, token=token)
        token = self.oauth.refresh_token(self.access_token_url,
                                         client_id=self.client_id,
                                         client_secret=self.client_secret)
        # set scope manually
        token['scope'] = self.scope
        return token

    def user_authorization(self):
        '''
        Implelent user behaviour: login and approve app permissions request
        '''
        response = self.authorization_get_request()
        response = self.authorization_post_request(response)
        return self.process_authorization_response(response)

    def process_authorization_response(self, response):
        url = self.get_url_from_response(response)
        if url:
            return url

        # TODO: handle this branch
        import ipdb
        ipdb.set_trace()

    def authorization_get_request(self):
        authorization_url = self.oauth.authorization_url(self.authorize_url)
        if self.type == 'oauth2':
            authorization_url, state = authorization_url
        return self.auth_request.session.get(url=authorization_url, headers=self.auth_request.headers)

    def authorization_post_request(self, response):
        method, action, data = self.auth_request.get_form_data_from_content(response.content)
        return getattr(self.auth_request.session, method)(url=action, headers=self.auth_request.headers, data=data)

    def get_url_from_response(self, response):
        raise NotImplementedError

    @abstractproperty
    def provider(self):
        pass

    @abstractproperty
    def authorize_url(self):
        pass

    @abstractproperty
    def access_token_url(self):
        pass

    @abstractproperty
    def auth_request_class(self):
        pass


class AuthRequestBase(object, SettingsMixin):

    __metaclass__ = ABCMeta

    authorize_form_attributes = {}

    session = None
    headers = {}

    @abstractproperty
    def form_action_domain(self):
        pass

    def __init__(self, username=None, password=None, additional=None):
        self.session = requests.Session()

        self.username = username or self.get_setting('username')
        self.password = password or self.get_setting('password')
        self.additional = additional or self.get_setting('additional')

    def authorized_request(self, method='get', **kwargs):
        if method not in ['get', 'post']:
            raise ValueError('Only `get` and `post` are allowed methods')

        if not self.session.cookies:
            self.authorize()

        if self.session.cookies:
            return getattr(self.session, method)(headers=kwargs.pop('headers', self.headers), **kwargs)
        else:
            raise ValueError('Session not defined')

    def authorize(self):
        '''
        Authorize and set self.session for next requests and return response of last request
        '''

        response = self.session.get(self.login_url, headers=self.headers)

        method, action, data = self.get_form_data_from_content(response.content, **self.authorize_form_attributes)

        # submit auth form data
        return self.session.post(action, data, headers=self.headers)

    def get_form_data(self, form):
        data = {}
        for input in form.findAll('input'):
            if input.get('name'):
                data[input.get('name')] = input.get('value')

        self.add_data_credentials(data)

        action = form.get('action')
        if action[0] == '/':
            action = self.form_action_domain + action

        return (form.get('method').lower(), action, data)

    @abstractmethod
    def add_data_credentials(self, data):
        pass

    def get_form_data_from_content(self, content, **kwargs):
        bs = BeautifulSoup(content)
        form = self.get_form_from_bs_content(bs, **kwargs)
        return self.get_form_data(form)

    def get_form_from_bs_content(self, bs, **kwargs):
        form = bs.find('form', **kwargs)
        if not form:
            raise Exception('There is no any form in response')
        return form
