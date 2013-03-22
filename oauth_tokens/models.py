from django.db import models
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.importlib import import_module

HISTORY = getattr(settings, 'OAUTH_TOKENS_HISTORY', False)
PROVIDERS = getattr(settings, 'OAUTH_TOKENS_PROVIDERS', {
    'vkontakte': 'oauth_tokens.providers.vkontakte.VkontakteAccessToken',
    'facebook': 'oauth_tokens.providers.facebook.FacebookAccessToken',
})
PROVIDER_CHOICES = [((provider, provider.title())) for provider in PROVIDERS.keys()]

class AccessTokenManager(models.Manager):
    '''
    Defautl manager for AccessToken for retrieving token
    '''
    def get_from_provider(self, provider):
        '''
        Get new token and save it to database. After it clean database if OAUTH_TOKENS_HISTORY disabled
        '''
        if provider not in PROVIDERS:
            raise ValueError("Provider `%s` not in available providers list" % provider)

        try:
            path = PROVIDERS[provider].split('.')
            module = '.'.join(path[:-1])
            class_name = path[-1]
            token_class = getattr(import_module(module), path[-1])
        except ImportError:
            raise ImproperlyConfigured("Impossible to find access token class with path %s" % PROVIDERS[provider])

        token = token_class().get()
        if not token:
            raise Exception("Error while getting new token")

        if not HISTORY:
            self.filter(provider=provider).delete()

        access_token = self.model(provider=provider)
        access_token.__dict__.update(token.__dict__)
        access_token.save()
        return access_token

class AccessToken(models.Model):
    class Meta:
        verbose_name = 'Oauth access token'
        verbose_name_plural = 'Oauth access tokens'
        ordering = ('-granted',)
        get_latest_by = 'granted'

    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    granted = models.DateTimeField(auto_now=True)

    access_token = models.CharField(max_length=200)
    expires = models.DateTimeField(null=True, blank=True)
    token_type = models.CharField(max_length=200, null=True, blank=True)
    refresh_token = models.CharField(max_length=200, null=True, blank=True)
    scope = models.CharField(max_length=200, null=True, blank=True)

    objects = AccessTokenManager()

    def __str__(self):
        return '#%s' % self.access_token