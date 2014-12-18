# -*- coding: utf-8 -*-
import cgi
import logging
import re
import urllib
from xml.sax import saxutils as su

from bs4 import BeautifulSoup
from django.core.exceptions import ImproperlyConfigured
import requests

from ..base import BaseAccessToken, AccessTokenBase, AccountLocked, AuthRequestBase, WrongRedirectUrl

log = logging.getLogger('oauth_tokens')


class FacebookAccessToken(BaseAccessToken):

    provider = 'facebook'
    authenticate_url = 'https://www.facebook.com/dialog/oauth'
    access_token_url = 'https://graph.facebook.com/oauth/access_token'
    redirect_uri = 'http://www.facebook.com/page_not_found'
    response_decoder = lambda self, x: dict(cgi.parse_qsl(x))
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/34.0.1847.116 Chrome/34.0.1847.116 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Charset': 'windows-1251,utf-8;q=0.7,*;q=0.3',
        'Accept-Encoding': 'gzip,deflate,sdch',
        'Accept-Language': 'en-US,en;q=0.8',
        'Connection': 'keep-alive',
        'Host': 'www.facebook.com',
    }

    def parse_auth_form(self, page_content):
        '''
        Parse page with auth form and return tuple with (method, form action, form submit parameters)
        DEPRECATED in favour FacebookAuthRequest
        '''
        content = BeautifulSoup(page_content)

        if content.find('title').text == 'Error':
            raise WrongRedirectUrl(content.find('div').text)

        form = content.find('form')
        if not form:
            raise Exception('There is no any form in response')

        method, action, data = self.get_form_attributes(form)

        data['email'] = self.username
        data['pass'] = self.password

        return (method, action, data)

    def get_form_attributes(self, form):
        '''
        DEPRECATED in favour FacebookAuthRequest
        '''
        data = {}
        for input in form.findAll('input'):
            if input.get('name'):
                data[input.get('name')] = input.get('value')

        action = form.get('action')
        if action[0] == '/':
            action = 'https://facebook.com' + action

        return (form.get('method').lower(), action, data)

    def parse_permissions_form(self, page_content):
        '''
        Parse page with permissions form and return tuple with (method, form action, form submit parameters)
        '''
        if '{"__html":"\u003Cform' in page_content:
            matches = re.findall(r'{"__html":"(\\u003Cform.+/form>)"},', page_content)
            content = BeautifulSoup(matches[0].decode("unicode-escape").replace('\/', '/'))
            form = content.find('form')
        else:
            content = BeautifulSoup(page_content)
            form = content.find('form', {'id': 'uiserver_form'})

        if not form:
            raise Exception('There is no any form in response')

        data = {}
        for input in form.findAll('input'):
            if input.get('name'):
                data[input.get('name')] = input.get('value')

        if 'cancel_clicked' in data:
            del data['cancel_clicked']

        action = form.get('action')
        if action[0] == '/':
            action = 'https://facebook.com' + action

        return (form.get('method').lower(), action, data)

    def authorize(self):
        '''
        Handling specific errors
        DEPRECATED in favour FacebookAuthRequest
        '''
        response = super(FacebookAccessToken, self).authorize()

        if 'You are trying too often' in response.content:
            # TODO: fix it
            log.error("Facebook authorization request returns error 'You are trying too often'")
            raise Exception("Facebook authorization request returns error 'You are trying too often'")
        if 'Cookies Required' in response.content:
            response = requests.get('http://facebook.com')
            self.cookies = response.cookies
            self.authorize()
        if 'API Error Code: 191' in response.content:
            raise ImproperlyConfigured(
                "You must specify URL '%s' in your facebook application settings" % self.redirect_uri)

        if 'Your account is temporarily locked.' in response.content:
            raise AccountLocked("Facebook errored 'Your account is temporarily locked.'. Try to login via web browser")

        if 'Redirecting...' in response.content:
            matches = re.findall(r'<meta http-equiv="refresh" content="0;url=(.+)" /></head>', response.content)
            url = su.unescape(urllib.unquote(matches[0]))
            response = requests.get(url, headers=self.headers, cookies=self.cookies)

        return response


class FacebookAuthRequest(AuthRequestBase):

    '''
    Facebook authorized request class
    '''
    provider = 'facebook'
    form_action_domain = 'https://facebook.com'
    login_url = 'https://www.facebook.com/login.php'
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/34.0.1847.116 Chrome/34.0.1847.116 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Charset': 'utf-8;q=0.7,*;q=0.3',
        'Accept-Encoding': 'gzip,deflate,sdch',
        'Accept-Language': 'en-US,en;q=0.8',
        'Connection': 'keep-alive',
        'Host': 'www.facebook.com',
    }

    account_locked_phrases = [
        'Ваш аккаунт временно заблокирован',
        'Your account is temporarily locked.',
    ]

    def add_data_credentials(self, data):
        data['email'] = self.username
        data['pass'] = self.password

    def authorize(self):
        '''
        TODO: cover with tests for each condition
        '''
        response = super(FacebookAuthRequest, self).authorize()

        if 'You are trying too often' in response.content:
            # TODO: fix it
            log.error("Facebook authorization request returns error 'You are trying too often'")
            raise Exception("Facebook authorization request returns error 'You are trying too often'")

        if 'Cookies Required' in response.content:
            response = requests.get(self.form_action_domain)
            self.cookies = response.cookies
            self.authorize()

        # TODO: move this to FacebookAcessToken class
        if 'API Error Code: 191' in response.content:
            raise ImproperlyConfigured(
                "You must specify URL '%s' in your facebook application settings" % self.redirect_uri)

        for account_locked_phrase in self.account_locked_phrases:
            if account_locked_phrase in response.content:
                raise AccountLocked(
                    "Facebook errored 'Your account is temporarily locked.'. Try to login via web browser")

        return response


class FacebookAccessTokenNew(AccessTokenBase):

    provider = 'facebook'
    type = 'oauth2'

    authorize_url = 'https://www.facebook.com/dialog/oauth'
    access_token_url = 'https://graph.facebook.com/oauth/access_token'

    redirect_uri = 'https://google.com/404'

    auth_request_class = FacebookAuthRequest

    def authorization_get_request(self):
        response = super(FacebookAccessTokenNew, self).authorization_get_request()

        bs = BeautifulSoup(response.content)
        if bs.find('title').text == 'Error':
            raise WrongRedirectUrl(bs.find('div').text)

        return response

    def authorization_post_request(self, response):
        response = super(FacebookAccessTokenNew, self).authorization_post_request(response)

        if 'Redirecting...' in response.content:
            matches = re.findall(r'<meta http-equiv="refresh" content="0;url=(.+)" /></head>', response.content)
            url = su.unescape(urllib.unquote(matches[0]))
            response = self.oauth.request(
                method='get', url=url, cookies=response.cookies, headers=self.auth_request.headers)

        return response

    def get_url_from_response(self, response):
        if response.status_code == 404 and 'code=' in response.url:
            return response.url
        else:
            return None
