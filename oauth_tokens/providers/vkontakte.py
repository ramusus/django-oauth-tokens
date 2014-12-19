# -*- coding: utf-8 -*-
import re

from bs4 import BeautifulSoup
import requests

from ..base import AccessTokenBase, AuthRequestBase, log
from ..exceptions import LoginPasswordError, AccountLocked, WrongRedirectUrl


class VkontakteAuthRequest(AuthRequestBase):

    '''
    Vkontakte authorized request class
    '''
    provider = 'vkontakte'
    form_action_domain = 'https://vk.com'
    login_url = 'http://vk.com/login.php'
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip,deflate,sdch',
        'Accept-Language': 'en-US,en;q=0.8',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Referer': 'http://vk.com/',
        'User-Agent': 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/30.0.1599.114 Chrome/30.0.1599.114 Safari/537.36',
    }

    def add_data_credentials(self, data):
        data['email'] = self.username
        data['pass'] = self.password

    def authorized_request(self, method='get', **kwargs):
        '''
        Protection with security question about part of phone number
        '''
        response = super(VkontakteAuthRequest, self).authorized_request(method=method, **kwargs)

        # TODO: test it and may be move to authorize() method
        if '<input name="code" id="code" type="text" class="text"' in response.content:
            m = re.findall(
                r"var params = {act: 'security_check', code: ge\('code'\).value, to: '([^']+)', al_page: '4', hash: '([^']+)'};", response.content)

            if len(m) == 0:
                raise Exception("Impossible to find security check parameters")

            additional = self.get_setting('additional')
            response = requests.post(self.login_url,
                                     headers={'X-Requested-With': 'XMLHttpRequest'},
                                     cookies=response.cookies,
                                     data={'act': 'security_check', 'code': additional, 'to': m[0][0], 'al_page': '4', 'hash': m[0][1]})

        return response

    def authorize(self):
        '''
        TODO: cover with tests for each condition
        '''
        response = super(VkontakteAuthRequest, self).authorize()

        if 'Invalid login or password.' in response.content:
            raise LoginPasswordError(
                u'Vkontakte auth error: Invalid login or password error. username: %s' % self.username)

        if 'act=blocked' in response.url:
            content = BeautifulSoup(response.content)
            reason = content.find('div', **{'class': re.compile('login_blocked_panel$')}).text
            raise AccountLocked(u"User %s for provider %s is blocked for reason: %s" %
                                (self.user.name, self.provider, reason))

        return response


class VkontakteAccessToken(AccessTokenBase):

    provider = 'vkontakte'
    type = 'oauth2'

    authorize_url = 'https://api.vk.com/oauth/authorize'
    access_token_url = 'https://api.vk.com/oauth/access_token'

    redirect_uri = 'https://api.vk.com/blank.html'

    auth_request_class = VkontakteAuthRequest

    def authorization_permissions_request(self, response):
        if response.status_code == 200 and 'https://oauth.vk.com/authorize' in response.url:
            matches = re.findall('location.href = "([^"]+https=1)"', response.content)
            if len(matches) != 1:
                raise Exception('Error while parsing permissions page contents')

            # without headers, otherwise bad response:
            # response.url == u'https://oauth.vk.com/error?err=2'
            # response.content == {"error":"invalid_request","error_description":"Security Error"}
            response = self.auth_request.session.get(url=matches[0])
            log.debug(response.url)

        return response

    def get_url_from_response(self, response):
        if response.status_code == 200 and 'code=' in response.url:
            return response.url.replace('#', '?')
        else:
            return None
