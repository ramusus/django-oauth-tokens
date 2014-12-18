
from datetime import timedelta

from django.utils import timezone
import factory

from .models import AccessToken, UserCredentials


class UserCredentialsFactory(factory.DjangoModelFactory):
    FACTORY_FOR = UserCredentials


class AccessTokenFactory(factory.DjangoModelFactory):
    FACTORY_FOR = AccessToken

    user = factory.SubFactory(UserCredentialsFactory)
    expires = timezone.now() + timedelta(1)
