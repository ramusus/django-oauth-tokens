# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import logging

from annoying.fields import JSONField
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils.importlib import import_module
from requests_oauthlib.oauth1_session import TokenRequestDenied
from taggit.managers import TaggableManager

from .exceptions import AccountLocked, LoginPasswordError, WrongAuthorizationResponseUrl

try:
    from django.db.transaction import atomic
except ImportError:
    from django.db.transaction import commit_on_success as atomic


log = logging.getLogger('oauth_tokens')

HISTORY = getattr(settings, 'OAUTH_TOKENS_HISTORY', False)
PROVIDERS = [
    'vkontakte',
    'facebook',
    'twitter',
    'odnoklassniki',
    'instagram',
]
PROVIDER_CHOICES = [((provider, provider.title())) for provider in PROVIDERS]
ACCESS_TOKENS_CLASSES = getattr(settings, 'OAUTH_TOKENS_CLASSES',
                                dict([(p, 'oauth_tokens.providers.%s.%sAccessToken' % (p, p.title()))
                                      for p in PROVIDERS])
                                )


class AccessTokenGettingError(Exception):
    pass


class AccessTokenRefreshingError(Exception):
    pass


class AccessTokenManager(models.Manager):

    '''
    Default manager for AccessToken for retrieving token
    '''

    def filter(self, *args, **kwargs):
        '''
        Optional filter by user's `tag`
        '''
        tag = kwargs.pop('tag', None)
        if tag:
            kwargs['user_credentials__in'] = UserCredentials.objects.filter(
                tags__name__in=[tag]).values_list('pk')

        return super(AccessTokenManager, self).filter(*args, **kwargs)

    def filter_active_tokens_of_provider(self, provider, *args, **kwargs):
        # don't use timezone.now() for ability to cache querysets
        next_hour = datetime(datetime.now().year,
                             datetime.now().month,
                             datetime.now().day,
                             datetime.now().hour) + timedelta(hours=1)
        return self.filter(provider=provider, expires_at__gt=next_hour, *args, **kwargs).order_by('?')

    def get_token(self, provider, tag=None):
        '''
        Returns access token instance. If tag argument provided or
        settings OAUTH_TOKENS_%s_USERNAME is not defined look up for credentials in DB
        '''
        if tag is None and getattr(settings, 'OAUTH_TOKENS_%s_USERNAME' % provider.upper(), None):
            user = None
        else:
            qs_users = UserCredentials.objects.filter(provider=provider)
            if tag:
                qs_users = qs_users.filter(tags__name__in=[tag])

            try:
                user = qs_users[0]
            except IndexError:
                raise Exception("User with tag %s for provider %s does not exist" % (tag, provider))

        return self.get_token_for_user(provider, user)

    def get_token_for_user(self, provider, user):
        token_class = self.get_token_class(provider)
        return self.get_token_of_class(token_class, user)

    def get_token_of_class(self, token_class, user=None):
        if user:
            return token_class(username=user.username, password=user.password, additional=user.additional)
        else:
            return token_class()

    def get_token_class(self, provider):

        if provider not in PROVIDERS:
            raise ValueError("Provider `%s` not in available providers list" % provider)

        try:
            path = ACCESS_TOKENS_CLASSES[provider].split('.')
            module = '.'.join(path[:-1])
            class_name = path[-1]
            token_class = getattr(import_module(module), path[-1])
        except ImportError:
            raise ImproperlyConfigured("Impossible to find access token class with path %s" %
                                       ACCESS_TOKENS_CLASSES[provider])

        return token_class

    def refresh(self, provider):
        '''
        Refresh tokens and save as new save it to database
        '''
        tokens = AccessToken.objects.filter(provider=provider).order_by('-id')

        access_tokens = []
        # TODO: remove limit for queryset, but handle behaviour with old accesstokens
        for token in tokens[:1]:
            token_class = self.get_token_class(provider)

            try:
                new_token = token_class().refresh(token)
            except:
                return self.fetch(provider)

            access_token = self.model.objects.create(provider=provider, user_credentials=user, **token)
            access_tokens += [access_token]

        if len(access_tokens) == 0:
            raise AccessTokenRefreshingError("No tokens refreshed for provider %s" % provider)

        return access_tokens

    @atomic
    def fetch(self, provider):
        '''
        Get new token and save it to database for all users in UserCredentials table.
        Сlean database before if OAUTH_TOKENS_HISTORY disabled
        '''
        token_class = self.get_token_class(provider)

        # walk through all users of current provider in UserCredentials table
        # or try to get user credentials from settings
        users = UserCredentials.objects.filter(provider=provider, active=True)
        if users.count() == 0:
            users = [None]

        access_tokens = AccessToken.objects.none()

        for user in users:

            try:
                token = self.get_token_of_class(token_class, user).get()
            except (TokenRequestDenied, AccountLocked, LoginPasswordError, WrongAuthorizationResponseUrl), e:
                log.error(u"Error '%s' while getting new token for provider %s and user %s" % (e, provider, user))
                user.inactivate(e)
                continue

            if not HISTORY:
                self.filter(provider=provider, user_credentials=user).delete()

            access_token = self.model.objects.create(provider=provider, user_credentials=user, **token)
            access_tokens |= AccessToken.objects.filter(pk=access_token.pk)

        if access_tokens.count() == 0:
            raise AccessTokenGettingError("No tokens for provider %s" % provider)

        return access_tokens


class AccessToken(models.Model):

    class Meta:
        verbose_name = 'Oauth access token'
        verbose_name_plural = 'Oauth access tokens'
        ordering = ('-granted_at',)
        get_latest_by = 'granted_at'

    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, db_index=True)
    granted_at = models.DateTimeField(auto_now=True)

    access_token = models.CharField(max_length=500)
    refresh_token = models.CharField(max_length=200, null=True, blank=True)

    expires_in = models.PositiveIntegerField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)

    token_type = models.CharField(max_length=200, null=True, blank=True)
    scope = JSONField(max_length=200, null=True, blank=True)

    # vk.com returns
    user_id = models.BigIntegerField(null=True, blank=True)

    user_credentials = models.ForeignKey('UserCredentials', null=True, blank=True)

    objects = AccessTokenManager()

    def __init__(self, *args, **kwargs):
        if 'expires_at' in kwargs and isinstance(kwargs['expires_at'], (float, int)):
            kwargs['expires_at'] = datetime.fromtimestamp(kwargs['expires_at'])
        super(AccessToken, self).__init__(*args, **kwargs)

    def __str__(self):
        return '#%s' % self.access_token


class UserCredentials(models.Model):

    name = models.CharField(max_length=100)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    active = models.BooleanField(default=True)
    exception = models.TextField(blank=True)

    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    additional = models.CharField(max_length=100, blank=True)

    tags = TaggableManager(blank=True)

    def __unicode__(self):
        return self.name

    def inactivate(self, error):
        self.exception = unicode(error)
        self.active = False
        self.save()

    def save(self, *args, **kwargs):
        if self.active:
            self.exception = ''
        super(UserCredentials, self).save(*args, **kwargs)
