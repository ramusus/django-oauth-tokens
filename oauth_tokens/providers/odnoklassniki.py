# -*- coding: utf-8 -*-
from ..base import AccessTokenBase, AuthRequestBase, log
from ..exceptions import LoginPasswordError, AccountLocked, WrongRedirectUrl


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


class OdnoklassnikiAccessToken(AccessTokenBase):

    provider = 'odnoklassniki'
    type = 'oauth2'

    authorize_url = 'https://ok.ru/oauth/authorize'
    access_token_url = 'https://api.ok.ru/oauth/token.do'

    redirect_uri = 'http://ok.ru'
    auth_request_class = OdnoklassnikiAuthRequest

    def set_auth_request(self, **kwargs):
        super(OdnoklassnikiAccessToken, self).set_auth_request(**kwargs)
        self.auth_request.form_action_domain = self.auth_request.form_action_domain.replace('https', 'http')

    def authorization_permissions_request(self, response):
        # TODO: needs tests
        if 'OAuth2Permissions' in response.content:
            method, action, data = self.auth_request.get_form_data_from_content(response.content)
            data.update({
                'button_accept_request': 'clicked',
                'hook_form_button_click': 'button_accept_request',
            })
            response = getattr(self.auth_request.session, method)(
                url=action, headers=self.auth_request.headers, data=data)
            log.debug(response.url)

        return response

    def get_url_from_response(self, response):
        if response.status_code == 200 and 'code=' in response.url:
            return response.url.replace('http', 'https')
        else:
            return None
