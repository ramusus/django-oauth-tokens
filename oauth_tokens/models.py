from django.db import models

PROVIDER_CHOICES = (
    ('vkontakte', 'Vkontate'),
    ('facebook', 'Facebook'),
)

class AccessToken(models.Model):
    class Meta:
        verbose_name = 'Oauth access token'
        verbose_name_plural = 'Oauth access tokens'

    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    granted = models.DateTimeField(auto_now=True)

    access_token = models.CharField(max_length=200)
    token_type = models.CharField(max_length=200)
    expires = models.DateTimeField()
    refresh_token = models.CharField(max_length=200)
    scope = models.CharField(max_length=200)