# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup

from ..base import AccessTokenBase, AuthRequestBase, log
from ..exceptions import LoginPasswordError, AccountLocked, WrongRedirectUrl


class TwitterAuthRequest(AuthRequestBase):

    '''
    Twitter authorized request class
    '''
    provider = 'twitter'
    form_action_domain = 'https://twitter.com'
    login_url = 'https://twitter.com/login'
    authorize_form_attributes = {"class_": "signin"}
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Origin': 'https://api.twitter.com',
        'X-DevTools-Emulate-Network-Conditions-Client-Id': 'F17D2F59-8F26-46F6-8C2C-E52E8CA7B56D',
        'User-Agent': 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/39.0.2171.65 Chrome/39.0.2171.65 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': 'https://api.twitter.com/oauth/authorize?oauth_token=prWUDG4s5HpwEnPY3Pun1CDgsXSVlfIU',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-US,en;q=0.8',
    }

    def add_data_credentials(self, data):
        data['session[username_or_email]'] = self.username
        data['session[password]'] = self.password
        if 'cancel' in data:
            del data['cancel']


class TwitterAccessToken(AccessTokenBase):

    provider = 'twitter'
    type = 'oauth1'

    authorize_url = 'https://api.twitter.com/oauth/authorize'
    access_token_url = 'https://api.twitter.com/oauth/access_token'
    request_token_url = 'https://api.twitter.com/oauth/request_token'

    auth_request_class = TwitterAuthRequest

    delimeter = '----------'

    def get(self):
        oauth_token = super(TwitterAccessToken, self).get()
        # {u'oauth_token_secret': u'TpAiPg7133dJKto5QK7UeIf968w1Ml26j3Yuzwp6vmkqU',
        # u'user_id': u'2931210558',
        # u'oauth_token': u'2931210558-1jnO1KLQV4Ru26o8Jr1nitsarSeDyKRLnEhcLvr',
        # u'screen_name': u'travis_djangov'}
        return {'access_token': self.delimeter.join([oauth_token.get('oauth_token'), oauth_token.get('oauth_token_secret')]),
                'user_id': oauth_token.get('user_id')}

    def authorization_get_request(self):
        authorization_url = self.oauth.authorization_url(self.authorize_url)
        return self.auth_request.session.get(url=authorization_url)  # twitter don't like headers here

    def process_authorization_response(self, response):
        bs = BeautifulSoup(response.content)
        try:
            code = int(bs.find('code').text)
        except:
            raise Exception("Wrong response on authorization post request for user %s" % self.auth_request.username)

        log.debug('Got twitter verifier: %s for user %s' % (code, self.auth_request.username))
        return str(code)
