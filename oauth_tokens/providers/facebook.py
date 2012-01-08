# -*- coding: utf-8 -*-
from oauth_tokens.base import BaseAccessToken
import cgi

class FacebookAccessToken(BaseAccessToken):

    provider = 'facebook'
    authenticate_url = 'https://www.facebook.com/dialog/oauth'
    access_token_url = 'https://graph.facebook.com/oauth/access_token'
    response_decoder = lambda x: dict(cgi.parse_qsl(x))

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
