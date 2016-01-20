from abc import ABCMeta, abstractproperty, abstractmethod
import logging

from bs4 import BeautifulSoup
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import requests
from requests_oauthlib import OAuth1Session, OAuth2Session

from .exceptions import WrongAuthorizationResponseUrl
from .models import UserCredentials

log = logging.getLogger('oauth_tokens')


class SettingsMixin:

    def get_setting(self, key):
        return getattr(settings, 'OAUTH_TOKENS_%s_%s' % (self.provider.upper(), key.upper()), None)


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
            raise ValueError('Session cookies are not defined')

    def authorize(self):
        """
        Authorize and set self.session for next requests and return response of last request
        """
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


class AccessTokenBase(object, SettingsMixin):

    __metaclass__ = ABCMeta

    def __init__(self, **kwargs):

        if self.type not in ['oauth1', 'oauth2']:
            raise ImproperlyConfigured("Property type should be equal 'oauth1' or 'oauth2'")

        if getattr(self, 'redirect_uri', None) is None:
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
        """
        Get and return access_token from provider using OAuth1 workflow
        Based on docs http://requests-oauthlib.readthedocs.org/en/latest/oauth1_workflow.html
        """
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
        return self.oauth.fetch_access_token(self.access_token_url)

    def oauth2_get(self):
        """
        Get and return access_token from provider using OAuth2 workflow
        Based on docs http://requests-oauthlib.readthedocs.org/en/latest/oauth2_workflow.html
        """
        self.oauth = OAuth2Session(self.client_id, redirect_uri=self.redirect_uri, scope=self.scope)

        authorization_response_url = self.user_authorization()
        # hack preventing to oauthlib comparing scope returned by response with initial
        # servers never returns scope parameter with token
        self.oauth.scope = None
        token = self.fetch_token(authorization_response_url)

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

    def fetch_token(self, authorization_response_url):
        return self.oauth.fetch_token(self.access_token_url,
                                       authorization_response=authorization_response_url,
                                       client_secret=self.client_secret)

    def user_authorization(self):
        """
        Implelent user behaviour: login and approve app permissions request
        """
        response = self.authorization_get_request()
        log.debug('auth get url: %s' % response.url)

        response = self.authorization_post_request(response)
        log.debug('auth post url: %s' % response.url)

        response = self.authorization_permissions_request(response)
        log.debug('auth perm url: %s' % response.url)

        return self.process_authorization_response(response)

    def process_authorization_response(self, response):
        url = self.get_url_from_response(response)
        if url:
            return url

        raise WrongAuthorizationResponseUrl("Wrong result url of authorization process: %s" % response.url)

    def authorization_get_request(self):
        return self.auth_request.session.get(url=self.get_authorization_url(), headers=self.auth_request.headers)

    def authorization_post_request(self, response):
        method, action, data = self.auth_request.get_form_data_from_content(response.content)
        return getattr(self.auth_request.session, method)(url=action, headers=self.auth_request.headers, data=data)

    def authorization_permissions_request(self, response):
        return response

    def get_authorization_url(self):
        authorization_url = self.oauth.authorization_url(self.authorize_url)
        if self.type == 'oauth2':
            authorization_url, state = authorization_url
        return authorization_url

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
