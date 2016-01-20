# -*- coding: utf-8 -*-
#from __future__ import unicode_literals
from datetime import datetime

from django.test import TestCase
import mock
import requests
from taggit.models import Tag

from .exceptions import LoginPasswordError, AccountLocked, WrongRedirectUrl
from .factories import AccessTokenFactory, UserCredentialsFactory
from .models import AccessToken, UserCredentials
from .providers.facebook import FacebookAccessToken, FacebookAuthRequest
from .providers.odnoklassniki import OdnoklassnikiAccessToken, OdnoklassnikiAuthRequest
from .providers.twitter import TwitterAccessToken, TwitterAuthRequest
from .providers.vkontakte import VkontakteAccessToken, VkontakteAuthRequest
from .providers.instagram import InstagramAccessToken, InstagramAuthRequest

TWITTER_CLIENT_ID = 'NLKrDQAE6YcSi76b0PGSg'
TWITTER_CLIENT_SECRET = '4D8TBznBjiJWlRE00G4qETLNNmfFadiKbREDrmNSDE'
TWITTER_USERNAME = 'baranus1@mail.ru'
TWITTER_PASSWORD = 'jcej9EIAQrrptDBy'
TWITTER_NAME = 'Travis Djangov'
TWITTER_SCREEN_NAME = '@travis_djangov'
TWITTER_USER_ID = 2931210558

VKONTAKTE_CLIENT_ID = 3430034
VKONTAKTE_CLIENT_SECRET = 'b0FwzyKtO8QiQmgWQMTz'
VKONTAKTE_SCOPE = ['ads', 'wall', 'photos', 'video', 'friends', 'stats', 'docs', 'notes']
VKONTAKTE_USERNAME = '+919665223715'
VKONTAKTE_PASSWORD = 'githubovich'
VKONTAKTE_ADDITIONAL = '96652237'
VKONTAKTE_NAME = 'Трэвис Джангов'
VKONTAKTE_USER_ID = 201164356

ODNOKLASSNIKI_CLIENT_ID = 1085608704
ODNOKLASSNIKI_CLIENT_SECRET = '1CEF9916FCDF50C873D231B3'
ODNOKLASSNIKI_SCOPE = ['VALUABLE_ACCESS']
ODNOKLASSNIKI_USERNAME = 'baranus1@mail.ru'
ODNOKLASSNIKI_PASSWORD = 'jcej9EIAQrrptDBy'
ODNOKLASSNIKI_NAME = 'Travis Djangov'

FACEBOOK_CLIENT_ID = 439210362826994
FACEBOOK_CLIENT_SECRET = '02569c93d18e4bc6aa210e594af84652'
FACEBOOK_SCOPE = ['read_stream']
FACEBOOK_USERNAME = '+919665223715'
FACEBOOK_PASSWORD = 'jcej9EIAQrrptDBy'
FACEBOOK_NAME = 'Travis Djangov'

INSTAGRAM_CLIENT_ID = 'fac34adbc6fd4f56803ec100234bf682'
INSTAGRAM_CLIENT_SECRET = '84a6a4732d31441d8794fd0e9cf6fe01'
INSTAGRAM_SCOPE = []
INSTAGRAM_USERNAME = 'atsepk'
INSTAGRAM_PASSWORD = 'fa54FsD'
INSTAGRAM_SCREEN_NAME = 'atsepk'


oauth2_token_mock_response = {'access_token': 's' * 81,
                              'refresh_token': 'e' * 41,
                              'token_type': 'session',
                              'expires_in': 86301,
                              'expires_at': 1418746001.153811,
                              'scope': VKONTAKTE_SCOPE,
                              'user_id': VKONTAKTE_USER_ID}


class OAuthTokensModelTest(TestCase):

    fixtures = ['oauth_tokens.usercredentials.json', ]

    def test_updating_vk(self):

        settings_temp = dict(OAUTH_TOKENS_VKONTAKTE_ADDITIONAL=VKONTAKTE_ADDITIONAL,
                             OAUTH_TOKENS_VKONTAKTE_SCOPE=VKONTAKTE_SCOPE,
                             OAUTH_TOKENS_VKONTAKTE_CLIENT_ID=VKONTAKTE_CLIENT_ID,
                             OAUTH_TOKENS_VKONTAKTE_CLIENT_SECRET=VKONTAKTE_CLIENT_SECRET)

        with self.settings(**settings_temp):
            self.assertEqual(AccessToken.objects.count(), 0)
            t = AccessToken.objects.fetch('vkontakte')
            self.assertGreater(AccessToken.objects.count(), 5)

    @mock.patch('oauth_tokens.base.AccessTokenBase.get', side_effect=lambda: dict(oauth2_token_mock_response))
    def test_creating_oauth2_token_model(self, method):

        AccessToken.objects.fetch('vkontakte')
        token = AccessToken.objects.all()[0]

        self.assertGreater(len(token.access_token), 80)
        self.assertGreater(len(token.refresh_token), 40)
        self.assertGreaterEqual(token.expires_in, 86300)
        self.assertIsInstance(token.expires_at, datetime)
        self.assertIsInstance(token.granted_at, datetime)
        self.assertEqual(token.scope, VKONTAKTE_SCOPE)
        self.assertEqual(token.user_id, VKONTAKTE_USER_ID)

    def test_creating_oauth1_token_model(self):

        UserCredentialsFactory(provider='twitter', username=TWITTER_USERNAME, password=TWITTER_PASSWORD)

        AccessToken.objects.fetch('twitter')
        token = AccessToken.objects.all()[0]

        self.assertEqual(len(token.access_token.split(TwitterAccessToken.delimeter)), 2)

    def test_methods_access_tag(self):

        user = UserCredentialsFactory(provider='vkontakte',
                                      username=VKONTAKTE_USERNAME, password=VKONTAKTE_PASSWORD, additional=VKONTAKTE_ADDITIONAL)
        user.tags.add(Tag.objects.create(name='ads'))

        for i in range(30):
            AccessTokenFactory(provider='vkontakte')
        access_token = AccessTokenFactory(provider='vkontakte', user_credentials=user)

        access_tokens = AccessToken.objects.filter_active_tokens_of_provider('vkontakte', tag='ads')
        self.assertEqual(access_tokens.count(), 1)
        self.assertEqual(access_token, access_tokens[0])

    def test_getting_token_by_tag(self):

        # get access token class with user credentials via interface
        settings_temp = dict(OAUTH_TOKENS_TWITTER_USERNAME=None,
                             OAUTH_TOKENS_TWITTER_PASSWORD=None)

        with self.settings(**settings_temp):
            user = UserCredentialsFactory(provider='twitter', username=TWITTER_USERNAME, password=TWITTER_PASSWORD)
            token = AccessToken.objects.get_token('twitter')

            self.assertEqual(token.auth_request.username, user.username)
            self.assertEqual(token.auth_request.password, user.password)

        # get access token class with user credentials via interface filtered by tag
        settings_temp = dict(OAUTH_TOKENS_VKONTAKTE_USERNAME=None,
                             OAUTH_TOKENS_VKONTAKTE_PASSWORD=None,
                             OAUTH_TOKENS_VKONTAKTE_ADDITIONAL=None)

        with self.settings(**settings_temp):
            user = UserCredentialsFactory(provider='vkontakte',
                                          username=VKONTAKTE_USERNAME, password=VKONTAKTE_PASSWORD, additional=VKONTAKTE_ADDITIONAL)
            user.tags.add(Tag.objects.create(name='ads'))

            token = AccessToken.objects.get_token('vkontakte', tag='ads')
            self.assertIsInstance(token, VkontakteAccessToken)
            self.assertEqual(token.auth_request.username, user.username)
            self.assertEqual(token.auth_request.password, user.password)
            self.assertEqual(token.auth_request.additional, user.additional)

        # get access token class with user credentials from settings via interface
        UserCredentials.objects.all().delete()
        settings_temp = dict(OAUTH_TOKENS_TWITTER_USERNAME=TWITTER_USERNAME,
                             OAUTH_TOKENS_TWITTER_PASSWORD=TWITTER_PASSWORD)

        with self.settings(**settings_temp):
            token = AccessToken.objects.get_token('twitter')

            self.assertEqual(token.auth_request.username, TWITTER_USERNAME)
            self.assertEqual(token.auth_request.password, TWITTER_PASSWORD)


class FacebookAccessTokenTest(TestCase):

    def assertFacebookToken(self, token):
        self.assertEqual(len(token), 4)
        self.assertGreater(len(token['access_token']), 160)
        self.assertGreaterEqual(token['expires_in'], 5000000)
        self.assertGreaterEqual(token['expires_at'], 1423930080.062079)
        self.assertEqual(token['scope'], FACEBOOK_SCOPE)

    def test_facebook_oauth_access_token(self):
        settings_temp = dict(OAUTH_TOKENS_FACEBOOK_USERNAME=FACEBOOK_USERNAME,
                             OAUTH_TOKENS_FACEBOOK_PASSWORD=FACEBOOK_PASSWORD,
                             OAUTH_TOKENS_FACEBOOK_REDIRECT_URI=None,
                             OAUTH_TOKENS_FACEBOOK_SCOPE=FACEBOOK_SCOPE,
                             OAUTH_TOKENS_FACEBOOK_CLIENT_ID=FACEBOOK_CLIENT_ID,
                             OAUTH_TOKENS_FACEBOOK_CLIENT_SECRET=FACEBOOK_CLIENT_SECRET)

        with self.settings(**settings_temp):
            self.assertFacebookToken(FacebookAccessToken().get())

    def test_facebook_oauth_access_token_user_in_db(self):
        settings_temp = dict(OAUTH_TOKENS_FACEBOOK_USERNAME=None,
                             OAUTH_TOKENS_FACEBOOK_PASSWORD=None,
                             OAUTH_TOKENS_FACEBOOK_REDIRECT_URI=None,
                             OAUTH_TOKENS_FACEBOOK_SCOPE=FACEBOOK_SCOPE,
                             OAUTH_TOKENS_FACEBOOK_CLIENT_ID=FACEBOOK_CLIENT_ID,
                             OAUTH_TOKENS_FACEBOOK_CLIENT_SECRET=FACEBOOK_CLIENT_SECRET)

        with self.settings(**settings_temp):
            self.assertFacebookToken(
                FacebookAccessToken(username=FACEBOOK_USERNAME, password=FACEBOOK_PASSWORD).get())

    def test_facebook_oauth_wrong_redirect_uri(self):
        settings_temp = dict(OAUTH_TOKENS_FACEBOOK_USERNAME=FACEBOOK_USERNAME,
                             OAUTH_TOKENS_FACEBOOK_PASSWORD=FACEBOOK_PASSWORD,
                             OAUTH_TOKENS_FACEBOOK_REDIRECT_URI='wrong',
                             OAUTH_TOKENS_FACEBOOK_CLIENT_ID=FACEBOOK_CLIENT_ID,
                             OAUTH_TOKENS_FACEBOOK_CLIENT_SECRET=FACEBOOK_CLIENT_SECRET)

        with self.settings(**settings_temp):
            with self.assertRaises(WrongRedirectUrl):
                access_token = FacebookAccessToken().get().access_token

    def test_facebook_authorized_request(self):
        settings_temp = dict(OAUTH_TOKENS_FACEBOOK_USERNAME=FACEBOOK_USERNAME,
                             OAUTH_TOKENS_FACEBOOK_PASSWORD=FACEBOOK_PASSWORD)

        with self.settings(**settings_temp):
            req = FacebookAuthRequest()

            response = requests.get(url=req.form_action_domain)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content.count(FACEBOOK_NAME), 0)

            response = req.authorized_request(url=req.form_action_domain)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content.count(FACEBOOK_NAME), 2)

            response = req.authorized_request(url='https://facebook.com')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content.count(FACEBOOK_NAME), 2)


class TwitterAccessTokenTest(TestCase):

    def assertTwitterToken(self, token_class, token):
        self.assertGreater(len(token['access_token']), 90)
        self.assertEqual(len(token['access_token'].split(token_class.delimeter)), 2)
        self.assertEqual(int(token['user_id']), TWITTER_USER_ID)

    def test_twitter_oauth_access_token(self):
        settings_temp = dict(OAUTH_TOKENS_TWITTER_USERNAME=TWITTER_USERNAME,
                             OAUTH_TOKENS_TWITTER_PASSWORD=TWITTER_PASSWORD,
                             OAUTH_TOKENS_TWITTER_CLIENT_ID=TWITTER_CLIENT_ID,
                             OAUTH_TOKENS_TWITTER_CLIENT_SECRET=TWITTER_CLIENT_SECRET)

        with self.settings(**settings_temp):
            token = TwitterAccessToken()
            self.assertTwitterToken(token, token.get())

    def test_twitter_oauth_access_token_user_in_db(self):
        settings_temp = dict(OAUTH_TOKENS_TWITTER_USERNAME=None,
                             OAUTH_TOKENS_TWITTER_PASSWORD=None,
                             OAUTH_TOKENS_TWITTER_CLIENT_ID=TWITTER_CLIENT_ID,
                             OAUTH_TOKENS_TWITTER_CLIENT_SECRET=TWITTER_CLIENT_SECRET)

        with self.settings(**settings_temp):
            token = TwitterAccessToken(username=TWITTER_USERNAME, password=TWITTER_PASSWORD)
            self.assertTwitterToken(token, token.get())

    def test_twitter_authorized_request(self):
        settings_temp = dict(OAUTH_TOKENS_TWITTER_USERNAME=TWITTER_USERNAME,
                             OAUTH_TOKENS_TWITTER_PASSWORD=TWITTER_PASSWORD)

        with self.settings(**settings_temp):
            req = TwitterAuthRequest()

            response = requests.get(url=req.form_action_domain)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content.count(TWITTER_SCREEN_NAME), 0)
            self.assertEqual(response.content.count(TWITTER_NAME), 0)

            response = req.authorized_request(url=req.form_action_domain)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content.count(TWITTER_SCREEN_NAME), 1)
            self.assertGreaterEqual(response.content.count(TWITTER_NAME), 3)


class VkontakteAccessTokenTest(TestCase):

    def assertVkontakteToken(self, token):
        self.assertEqual(len(token), 5)
        self.assertGreater(len(token['access_token']), 80)
        self.assertGreaterEqual(token['expires_in'], 86300)
        self.assertGreaterEqual(token['expires_at'], 1418746001.153811)
        self.assertEqual(token['scope'], VKONTAKTE_SCOPE)
        self.assertEqual(token['user_id'], VKONTAKTE_USER_ID)

    def test_vkontakte_oauth_access_token(self):
        settings_temp = dict(OAUTH_TOKENS_VKONTAKTE_USERNAME=VKONTAKTE_USERNAME,
                             OAUTH_TOKENS_VKONTAKTE_PASSWORD=VKONTAKTE_PASSWORD,
                             OAUTH_TOKENS_VKONTAKTE_ADDITIONAL=VKONTAKTE_ADDITIONAL,
                             OAUTH_TOKENS_VKONTAKTE_SCOPE=VKONTAKTE_SCOPE,
                             OAUTH_TOKENS_VKONTAKTE_CLIENT_ID=VKONTAKTE_CLIENT_ID,
                             OAUTH_TOKENS_VKONTAKTE_CLIENT_SECRET=VKONTAKTE_CLIENT_SECRET)

        with self.settings(**settings_temp):
            self.assertVkontakteToken(VkontakteAccessToken().get())

    def test_vkontakte_oauth_access_token_user_in_db(self):
        settings_temp = dict(OAUTH_TOKENS_VKONTAKTE_USERNAME=None,
                             OAUTH_TOKENS_VKONTAKTE_PASSWORD=None,
                             OAUTH_TOKENS_VKONTAKTE_ADDITIONAL=None,
                             OAUTH_TOKENS_VKONTAKTE_SCOPE=VKONTAKTE_SCOPE,
                             OAUTH_TOKENS_VKONTAKTE_CLIENT_ID=VKONTAKTE_CLIENT_ID,
                             OAUTH_TOKENS_VKONTAKTE_CLIENT_SECRET=VKONTAKTE_CLIENT_SECRET)

        with self.settings(**settings_temp):
            self.assertVkontakteToken(
                VkontakteAccessToken(username=VKONTAKTE_USERNAME, password=VKONTAKTE_PASSWORD).get())

    def test_vkontakte_login_password_error(self):
        settings_temp = dict(OAUTH_TOKENS_VKONTAKTE_USERNAME=VKONTAKTE_USERNAME,
                             OAUTH_TOKENS_VKONTAKTE_PASSWORD='wrong')

        with self.settings(**settings_temp):
            req = VkontakteAuthRequest()
            with self.assertRaises(LoginPasswordError):
                response = VkontakteAuthRequest().authorized_request(url=req.form_action_domain)

    def test_vkontakte_authorized_request(self):
        settings_temp = dict(OAUTH_TOKENS_VKONTAKTE_USERNAME=VKONTAKTE_USERNAME,
                             OAUTH_TOKENS_VKONTAKTE_PASSWORD=VKONTAKTE_PASSWORD,
                             OAUTH_TOKENS_VKONTAKTE_ADDITIONAL=VKONTAKTE_ADDITIONAL)

        with self.settings(**settings_temp):
            req = VkontakteAuthRequest()

            response = requests.get(url=req.form_action_domain)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content.count(VKONTAKTE_NAME), 0)

            response = req.authorized_request(url=req.form_action_domain)
            self.assertEqual(response.status_code, 200)
            self.assertGreaterEqual(response.content.decode('windows-1251').encode('utf-8').count(VKONTAKTE_NAME), 5)


class OdnoklassnikiAccessTokenTest(TestCase):

    def assertOdnoklassnikiToken(self, token):
        self.assertEqual(len(token), 4)
        self.assertGreater(len(token['access_token']), 20)
        self.assertGreater(len(token['refresh_token']), 40)
        self.assertEqual(token['token_type'], 'session')
        self.assertEqual(token['scope'], ODNOKLASSNIKI_SCOPE)

    def test_odnoklassniki_oauth_access_token(self):
        settings_temp = dict(OAUTH_TOKENS_ODNOKLASSNIKI_USERNAME=ODNOKLASSNIKI_USERNAME,
                             OAUTH_TOKENS_ODNOKLASSNIKI_PASSWORD=ODNOKLASSNIKI_PASSWORD,
                             OAUTH_TOKENS_ODNOKLASSNIKI_SCOPE=ODNOKLASSNIKI_SCOPE,
                             OAUTH_TOKENS_ODNOKLASSNIKI_CLIENT_ID=ODNOKLASSNIKI_CLIENT_ID,
                             OAUTH_TOKENS_ODNOKLASSNIKI_CLIENT_SECRET=ODNOKLASSNIKI_CLIENT_SECRET)

        with self.settings(**settings_temp):
            token = OdnoklassnikiAccessToken().get()
            self.assertOdnoklassnikiToken(token)

            token_new = OdnoklassnikiAccessToken().refresh(token)
            self.assertOdnoklassnikiToken(token_new)
            self.assertEqual(token['refresh_token'], token_new['refresh_token'])
            self.assertNotEqual(token['access_token'], token_new['access_token'])

    def test_odnoklassniki_authorized_request(self):
        settings_temp = dict(OAUTH_TOKENS_ODNOKLASSNIKI_USERNAME=ODNOKLASSNIKI_USERNAME,
                             OAUTH_TOKENS_ODNOKLASSNIKI_PASSWORD=ODNOKLASSNIKI_PASSWORD)

        with self.settings(**settings_temp):
            req = OdnoklassnikiAuthRequest()

            response = requests.get(url=req.form_action_domain)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content.count(ODNOKLASSNIKI_NAME), 0)

            response = OdnoklassnikiAuthRequest().authorized_request(url=req.form_action_domain)
            self.assertEqual(response.status_code, 200)
            self.assertGreater(response.content.count(ODNOKLASSNIKI_NAME), 0)


class InstagramAccessTokenTest(TestCase):

    def assertInstagramToken(self, token_class, token):
        self.assertGreater(len(token['access_token']), 40)
        # self.assertEqual(len(token['access_token'].split(token_class.delimeter)), 2)
        # self.assertEqual(int(token['user_id']), INSTAGRAM_USER_ID)

    def test_instagram_oauth_access_token(self):
        settings_temp = dict(OAUTH_TOKENS_INSTAGRAM_USERNAME=INSTAGRAM_USERNAME,
                             OAUTH_TOKENS_INSTAGRAM_PASSWORD=INSTAGRAM_PASSWORD,
                             OAUTH_TOKENS_INSTAGRAM_CLIENT_ID=INSTAGRAM_CLIENT_ID,
                             OAUTH_TOKENS_INSTAGRAM_CLIENT_SECRET=INSTAGRAM_CLIENT_SECRET)

        with self.settings(**settings_temp):
            token = InstagramAccessToken()
            self.assertInstagramToken(token, token.get())

    def test_instagram_oauth_access_token_user_in_db(self):
        settings_temp = dict(OAUTH_TOKENS_INSTAGRAM_USERNAME=None,
                             OAUTH_TOKENS_INSTAGRAM_PASSWORD=None,
                             OAUTH_TOKENS_INSTAGRAM_CLIENT_ID=INSTAGRAM_CLIENT_ID,
                             OAUTH_TOKENS_INSTAGRAM_CLIENT_SECRET=INSTAGRAM_CLIENT_SECRET)

        with self.settings(**settings_temp):
            token = InstagramAccessToken(username=INSTAGRAM_USERNAME, password=INSTAGRAM_PASSWORD)
            self.assertInstagramToken(token, token.get())

    def test_instagram_authorized_request(self):
        settings_temp = dict(OAUTH_TOKENS_INSTAGRAM_USERNAME=INSTAGRAM_USERNAME,
                             OAUTH_TOKENS_INSTAGRAM_PASSWORD=INSTAGRAM_PASSWORD)

        with self.settings(**settings_temp):
            req = InstagramAuthRequest()

            response = requests.get(url=req.form_action_domain)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content.count(INSTAGRAM_SCREEN_NAME), 0)

            response = req.authorized_request(url=req.form_action_domain)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content.count(INSTAGRAM_SCREEN_NAME), 1)
