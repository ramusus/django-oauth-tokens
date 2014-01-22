# -*- coding: utf-8 -*-
from django.core.exceptions import ImproperlyConfigured
from BeautifulSoup import BeautifulSoup
from oauth_tokens.base import BaseAccessToken, OAuthError
import requests
import re
import logging

log = logging.getLogger('oauth_tokens')

class VkontakteAccessToken(BaseAccessToken):

    provider = 'vkontakte'
    authenticate_url = 'https://api.vk.com/oauth/authorize'
    access_token_url = 'https://api.vk.com/oauth/access_token'
    redirect_uri = 'http://api.vk.com/blank.html'
    response_decoder = None
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip,deflate,sdch',
        'Accept-Language': 'en-US,en;q=0.8',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Cookie': 'audio_time_left=1; audio_vol=100; remixlang=0; remixexp=1; remixstid=992892995; remixdt=5400; remixrefkey=ce1feae619112813c2; remixvkcom=; remixtst=4dc9ab5b; remixrec_sid=; remixseenads=1; remixreg_sid=; remixlo_hash=; remixflash=11.2.202; remixscreen_depth=24; remixmid=; remixsid=; remixsid6=; remixgid=; remixemail=; remixpass=; remixapi_sid=; remixpermit=; remixsslsid=',
        'Pragma': 'no-cache',
        'Referer': 'http://vk.com/',
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

        data = {}
        for input in form.findAll('input'):
            if input.get('name'):
                data[input.get('name')] = input.get('value')

        data['email'] = self.username
        data['pass'] = self.password

        return (form.get('method').lower(), form.get('action'), data)

    def parse_permissions_form(self, page_content):
        '''
        Parse page with permissions form and return tuple with (method, form action, form submit parameters)
        '''
        matches = re.findall('location.href = "([^"]+https=1)"', page_content)
        if len(matches) != 1:
            log.error("Error while parsing permissions page contents: %s" % page_content)
            raise Exception('Error while parsing permissions page contents')

        return ('get', matches[0], {})

    def authorize(self):
        '''
        Protection from security question about end of phone number
        '''
        response = super(VkontakteAccessToken, self).authorize()

        if 'Invalid login or password.' in response.content:
            raise ImproperlyConfigured('Vkontakte auth error: Invalid login or password error')

        # login from new place
        if response.content == 'security breach':
            index_page = self.authorized_request(method='get', url='http://vk.com/')
            response = super(VkontakteAccessToken, self).authorize()
        elif response.content == '{"error":"invalid_request","error_description":"Security Error"}':
            # TODO: fix it
            log.error("Vkontakte authorization request returns error %s" % response.content)
            raise OAuthError("Vkontakte authorization request returns error %s" % response.content)

        # need approve for extra rights
        if 'function approve() {' in response.content:
            for url in re.findall(r'location.href = "([^"]+)"', response.content):
                if 'response_type=code' in url:
                    response = self.authorized_request(method='get', url=url)
                    break

        # first grant access question
        if '<form method="post" action="https://login.vk.com/?act=grant_access' in response.content:
            content = BeautifulSoup(response.content)
            form = content.find('form')
            response = requests.get(form['action'], cookies=response.cookies)

        # other grant access questions
        elif 'https://login.vk.com/?act=grant_access' in response.content:
            for url in re.findall(r'"(https:\/\/login.vk.com\/\?act=grant_access[^"]+)"', response.content):
                if 'cancel' not in url:
                    response = requests.get(url, cookies=response.cookies)
                    break

        if 'class="oauth_error"' in response.content:
            content = BeautifulSoup(response.content.decode('windows-1251'))
            raise OAuthError(content.find('div', **{'class': 'oauth_error'}).text.encode('utf-8'))

        return response

    def authorized_request(self, method='get', **kwargs):
        '''
        Protection from security question about end of phone number
        '''
        response = super(VkontakteAccessToken, self).authorized_request(method=method, **kwargs)

        if '<input name="code" id="code" type="text" class="text"' in response.content:
            m = re.findall(r"var params = {act: 'security_check', code: ge\('code'\).value, to: '([^']+)', al_page: '4', hash: '([^']+)'};", response.content)

            if len(m) == 0:
                raise Exception("Impossible to find security check parameters")

            response = requests.post('http://vk.com/login.php',
                headers = {'X-Requested-With': 'XMLHttpRequest'},
                cookies = response.cookies,
                data = {'act': 'security_check', 'code': self.get_setting('additional'), 'to': m[0][0], 'al_page': '4', 'hash': m[0][1]})

        return response