# -*- coding: utf-8 -*-
from django.test import TestCase
from models import AccessToken

class OAuthTokensTest(TestCase):

    def test_updating_vk(self):

        self.assertEqual(AccessToken.objects.count(), 0)
        t = AccessToken.objects.get_from_provider('vkontakte')
        self.assertEqual(AccessToken.objects.count(), 1)