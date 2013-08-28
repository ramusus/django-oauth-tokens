from models import AccessToken, UserCredentials
from datetime import datetime, timedelta
import factory

class UserCredentialsFactory(factory.DjangoModelFactory):
    FACTORY_FOR = UserCredentials

class AccessTokenFactory(factory.DjangoModelFactory):
    FACTORY_FOR = AccessToken

    user = factory.SubFactory(UserCredentialsFactory)
    expires = datetime.now()+timedelta(1)