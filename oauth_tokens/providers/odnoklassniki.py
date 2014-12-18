# -*- coding: utf-8 -*-
import logging
import re

from bs4 import BeautifulSoup
from django.core.exceptions import ImproperlyConfigured
import requests

from ..base import BaseAccessToken, AccessTokenBase, AuthRequestBase


log = logging.getLogger('oauth_tokens')


class OdnoklassnikiAccessToken(BaseAccessToken):

    provider = 'odnoklassniki'
    authenticate_url = 'http://www.odnoklassniki.ru/oauth/authorize'
    access_token_url = 'http://api.odnoklassniki.ru/oauth/token.do'
    redirect_uri = 'http://www.odnoklassniki.ru/'
    response_decoder = None
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip,deflate,sdch',
        'Accept-Language': 'en-US,en;q=0.8',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Cookie': 'audio_time_left=1; audio_vol=100; remixlang=0; remixexp=1; remixstid=992892995; remixdt=5400; remixrefkey=ce1feae619112813c2; remixvkcom=; remixtst=4dc9ab5b; remixrec_sid=; remixseenads=1; remixreg_sid=; remixlo_hash=; remixflash=11.2.202; remixscreen_depth=24; remixmid=; remixsid=; remixsid6=; remixgid=; remixemail=; remixpass=; remixapi_sid=; remixpermit=; remixsslsid=',
        'Pragma': 'no-cache',
        'Referer': 'http://www.odnoklassniki.ru/',
        'User-Agent': 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/30.0.1599.114 Chrome/30.0.1599.114 Safari/537.36',
    }

    def parse_auth_form(self, page_content):
        '''
        Parse page with auth form and return tuple with (method, form action, form submit parameters)
        '''
        content = BeautifulSoup(page_content)

        form = content.find('form')
        if not form:
            raise Exception('There is no any form in response')

        method, action, data = self.get_form_attributes(form)

        data['fr.email'] = self.username
        data['fr.password'] = self.password

        return (method, action, data)

    def get_form_attributes(self, form):
        data = {}
        for input in form.findAll('input'):
            if input.get('name'):
                data[input.get('name')] = input.get('value')

        action = form.get('action')
        if action[0] == '/':
            action = 'http://www.odnoklassniki.ru' + action

        return (form.get('method').lower(), action, data)

    def parse_permissions_form(self, page_content):
        '''
        Parse page with permissions form and return tuple with (method, form action, form submit parameters)
        '''
#        import ipdb; ipdb.set_trace()
        content = BeautifulSoup(page_content)

        form = content.find('form')
        if not form:
            raise Exception('There is no any form in response')

        return self.get_form_attributes(form)


class OdnoklassnikiAuthRequest(AuthRequestBase):

    provider = 'odnoklassniki'
    form_action_domain = 'https://ok.ru'
    login_url = 'https://ok.ru'
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip,deflate,sdch',
        'Accept-Language': 'en-US,en;q=0.8',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Cookie': 'audio_time_left=1; audio_vol=100; remixlang=0; remixexp=1; remixstid=992892995; remixdt=5400; remixrefkey=ce1feae619112813c2; remixvkcom=; remixtst=4dc9ab5b; remixrec_sid=; remixseenads=1; remixreg_sid=; remixlo_hash=; remixflash=11.2.202; remixscreen_depth=24; remixmid=; remixsid=; remixsid6=; remixgid=; remixemail=; remixpass=; remixapi_sid=; remixpermit=; remixsslsid=',
        'Pragma': 'no-cache',
        'Referer': 'http://ok.ru/',
        'User-Agent': 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/30.0.1599.114 Chrome/30.0.1599.114 Safari/537.36',
    }

    def add_data_credentials(self, data):
        for key, value in data.items():
            if 'email' in key:
                data[key] = self.username
            elif 'password' in key:
                data[key] = self.password


class OdnoklassnikiAccessTokenNew(AccessTokenBase):

    provider = 'odnoklassniki'
    type = 'oauth2'

    authorize_url = 'https://ok.ru/oauth/authorize'
    access_token_url = 'https://api.ok.ru/oauth/token.do'

    redirect_uri = 'http://ok.ru'
    auth_request_class = OdnoklassnikiAuthRequest

    def set_auth_request(self, **kwargs):
        super(OdnoklassnikiAccessTokenNew, self).set_auth_request(**kwargs)
        self.auth_request.form_action_domain = self.auth_request.form_action_domain.replace('https', 'http')

    def get_url_from_response(self, response):
        if response.status_code == 200 and 'code=' in response.url:
            return response.url.replace('http', 'https')
        else:
            return None
