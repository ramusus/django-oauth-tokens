
from datetime import timedelta

from django.utils import timezone
import factory

from .models import AccessToken, UserCredentials


class UserCredentialsFactory(factory.DjangoModelFactory):
    FACTORY_FOR = UserCredentials

    active = True


class AccessTokenFactory(factory.DjangoModelFactory):
    FACTORY_FOR = AccessToken

    user_credentials = factory.SubFactory(UserCredentialsFactory)
    expires_at = timezone.now() + timedelta(1)
