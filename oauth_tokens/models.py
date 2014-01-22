# -*- coding: utf-8 -*-
from django.db import models
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.importlib import import_module
from taggit.managers import TaggableManager
from datetime import datetime
import logging

log = logging.getLogger('oauth_tokens')

HISTORY = getattr(settings, 'OAUTH_TOKENS_HISTORY', False)
PROVIDERS = getattr(settings, 'OAUTH_TOKENS_PROVIDERS', {
    'vkontakte': 'oauth_tokens.providers.vkontakte.VkontakteAccessToken',
    'facebook': 'oauth_tokens.providers.facebook.FacebookAccessToken',
})
PROVIDER_CHOICES = [((provider, provider.title())) for provider in PROVIDERS.keys()]

class AccessTokenGettingError(Exception):
    pass

class AccessTokenManager(models.Manager):
    '''
    Defautl manager for AccessToken for retrieving token
    '''
    def filter(self, *args, **kwargs):
        '''
        Optional filter by user's `tag`
        '''
        tag = kwargs.pop('tag', None)
        if tag:
            kwargs['user__in'] = UserCredentials.objects.filter(tags__name__in=[tag]).values_list('pk', flat=True)

        return super(AccessTokenManager, self).filter(*args, **kwargs)

    def filter_active_tokens_of_provider(self, provider, *args, **kwargs):
        return self.filter(provider=provider, expires__gt=datetime.now(), *args, **kwargs).order_by('?')

    def fetch(self, provider):
        '''
        Get new token and save it to database for all users in UserCredentials table.
        Сlean database before if OAUTH_TOKENS_HISTORY disabled
        '''
        from base import OAuthError

        if provider not in PROVIDERS:
            raise ValueError("Provider `%s` not in available providers list" % provider)

        try:
            path = PROVIDERS[provider].split('.')
            module = '.'.join(path[:-1])
            class_name = path[-1]
            token_class = getattr(import_module(module), path[-1])
        except ImportError:
            raise ImproperlyConfigured("Impossible to find access token class with path %s" % PROVIDERS[provider])

        # walk through all users of current provider in UserCredentials table
        # or try to get user credentials from settings
        users = UserCredentials.objects.filter(provider=provider, active=True)
        if users.count() == 0:
            users = [None]

        access_tokens = []

        for user in users:

            try:
                token = token_class(user=user).get()
                assert token
            except OAuthError, e:
                log.error("Error '%s' while getting new token for provider %s and user %s" % (e, provider, user))
                continue

            if not HISTORY:
                self.filter(provider=provider, user=user).delete()

            access_token = self.model(provider=provider, user=user)
            access_token.__dict__.update(token.__dict__)
            access_token.save()
            access_tokens += [access_token]

        if len(access_tokens) == 0:
            raise AccessTokenGettingError("Error while updating tokens for provider %s" % provider)

        return access_tokens

class AccessToken(models.Model):
    class Meta:
        verbose_name = 'Oauth access token'
        verbose_name_plural = 'Oauth access tokens'
        ordering = ('-granted',)
        get_latest_by = 'granted'

    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    granted = models.DateTimeField(auto_now=True)

    access_token = models.CharField(max_length=500)
    expires = models.DateTimeField(null=True, blank=True)
    token_type = models.CharField(max_length=200, null=True, blank=True)
    refresh_token = models.CharField(max_length=200, null=True, blank=True)
    scope = models.CharField(max_length=200, null=True, blank=True)

    user = models.ForeignKey('UserCredentials', null=True, blank=True)

    objects = AccessTokenManager()

    def __str__(self):
        return '#%s' % self.access_token

class UserCredentials(models.Model):

    name = models.CharField(max_length=100)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    active = models.BooleanField()

    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    additional = models.CharField(max_length=100, blank=True)

    tags = TaggableManager(blank=True)

    def __unicode__(self):
        return self.name