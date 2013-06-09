# -*- coding: utf-8 -*-
from BeautifulSoup import BeautifulSoup
from oauth_tokens.base import BaseAccessToken
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
            raise Exception('Error while parsing permissions page contents')

        return ('get', matches[0], {})

    def authorize(self):
        '''
        Protection from security question about end of phone number
        '''
        response = super(VkontakteAccessToken, self).authorize()

        # login from new place
        if response.content == 'security breach':
            index_page = self.authorized_request(method='get', url='http://vk.com/')
            response = super(VkontakteAccessToken, self).authorize()
        elif response.content == '{"error":"invalid_request","error_description":"Security Error"}':
            # TODO: fix it
            log.error("Vkontakte authorization request returns error %s" % response.content)
            raise Exception("Vkontakte authorization request returns error %s" % response.content)

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
            response = requests.post(form['action'], cookies=response.cookies)

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
                data = {'act': 'security_check', 'code': self.get_setting('phone_end'), 'to': m[0][0], 'al_page': '4', 'hash': m[0][1]})

        return response
