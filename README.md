# Introduction

Application for getting, storing and refreshing OAuth access_tokens for
Django standalone applications without user manipulations.
Applications also can imitate authorized requests on behalf of user

# Providers

## Vkontakte

    OAUTH_TOKENS_VKONTAKTE_CLIENT_ID = ...
    OAUTH_TOKENS_VKONTAKTE_CLIENT_SECRET = ...
    OAUTH_TOKENS_VKONTAKTE_SCOPE = ['ads,wall,photos,friends,stats'] # array of strings
    OAUTH_TOKENS_VKONTAKTE_USERNAME = ...
    OAUTH_TOKENS_VKONTAKTE_PASSWORD = ...
    OAUTH_TOKENS_VKONTAKTE_PHONE_END = ... # last 4 digits

## Facebook

    OAUTH_TOKENS_FACEBOOK_CLIENT_ID = ...
    OAUTH_TOKENS_FACEBOOK_CLIENT_SECRET = ...
    OAUTH_TOKENS_FACEBOOK_SCOPE = ['offline_access'] # array of strings
    OAUTH_TOKENS_FACEBOOK_USERNAME = ...
    OAUTH_TOKENS_FACEBOOK_PASSWORD = ...

# Settings

    OAUTH_TOKENS_HISTORY = True # to keep in DB access tokens expired

# Dependencies

* Django
* oauth2 service depends on http://github.com/ryanhorn/tyoiOAuth2.git
* requests (pip install requests)