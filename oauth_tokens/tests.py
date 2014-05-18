# -*- coding: utf-8 -*-
from django.test import TestCase
from models import AccessToken, UserCredentials
from factories import AccessTokenFactory, UserCredentialsFactory
from taggit.models import Tag

class OAuthTokensTest(TestCase):
    fixtures = ['oauth_tokens.usercredentials.json',]

    def test_updating_vk(self):

        self.assertEqual(AccessToken.objects.count(), 0)
        t = AccessToken.objects.get_from_provider('vkontakte')
        self.assertTrue(AccessToken.objects.count() > 0)

    def test_methods_access_tag(self):

        user = UserCredentials.objects.all()[0]
        user.tags.add(Tag.objects.create(name='ads'))

        for i in range(30):
            AccessTokenFactory.create(provider='vkontakte')
        access_token = AccessTokenFactory.create(provider='vkontakte', user=user)

        access_tokens = AccessToken.objects.filter_active_tokens_of_provider('vkontakte', tag='ads')
        self.assertEqual(access_tokens.count(), 1)
        self.assertTrue(access_token in access_tokens)