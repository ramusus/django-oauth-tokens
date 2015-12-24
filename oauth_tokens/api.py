# -*- coding: utf-8 -*-
import logging
import socket
import sys
import time
import warnings
from abc import ABCMeta, abstractmethod, abstractproperty
from httplib import BadStatusLine, ResponseNotReady, IncompleteRead
from ssl import SSLError

from requests.exceptions import ConnectionError
from django.conf import settings
from django.test.utils import override_settings

from .models import AccessToken, AccessTokenGettingError, AccessTokenRefreshingError
from .lock import distributedlock, LockNotAcquiredError

__all__ = ['NoActiveTokens', 'ApiAbstractBase', 'Singleton']


class NoActiveTokens(Exception):
    pass


class ApiAbstractBase(object):
    __metaclass__ = ABCMeta

    consistent_token = None
    error_class = Exception
    error_class_repeat = (SSLError, ConnectionError, socket.error, BadStatusLine, ResponseNotReady, IncompleteRead)
    sleep_repeat_error_messages = []

    recursion_count = 0

    method = None
    token_tag = None
    token_tag_arg_name = 'methods_access_tag'
    user = None
    user_arg_name = 'user'
    used_access_tokens = None

    update_tokens_max_count = 5
    refresh_tokens_max_count = 5

    def __init__(self):
        self.used_access_tokens = []
        self.consistent_token = None
        self.logger = self.get_logger()
        self.api = None

    def set_context(self, **kwargs):
        # define context of call on each calling, becouse instanse is singleton
        self.user = self.token_tag = self.consistent_token = None

        if self.token_tag_arg_name in kwargs:
            warnings.warn('Kwarg `%s` is deprecated, use `OAUTH_TOKENS_API_CALL_CONTEXT` instead.'
                          % self.token_tag_arg_name, DeprecationWarning)
            self.token_tag = kwargs.pop(self.token_tag_arg_name, None)

        if self.user_arg_name in kwargs:
            warnings.warn('Kwarg `%s` is deprecated, use `OAUTH_TOKENS_API_CALL_CONTEXT` instead.'
                          % self.user_arg_name, DeprecationWarning)
            self.user = kwargs.pop(self.user_arg_name, None)

        context = getattr(settings, 'OAUTH_TOKENS_API_CALL_CONTEXT', None)
        if context and self.provider in context:
            if 'user' in context[self.provider]:
                self.user = context[self.provider]['user']
            if 'tag' in context[self.provider]:
                self.token_tag = context[self.provider]['tag']
            if 'token' in context[self.provider]:
                self.consistent_token = context[self.provider]['token']

    def call(self, method, *args, **kwargs):
        self.method = method
        self.set_context(**kwargs)

        try:
            token = self.get_token(tag=self.token_tag)
        except NoActiveTokens, e:
            return self.handle_error_no_active_tokens(e, *args, **kwargs)

        self.api = self.get_api(token)

        try:
            response = self.get_api_response(*args, **kwargs)
        except self.error_class, e:
            response = self.handle_error_message(e, *args, **kwargs)
            if response is not None:
                return response
            response = self.handle_error_code(e, *args, **kwargs)
        except self.error_class_repeat, e:
            response = self.handle_error_repeat(e, *args, **kwargs)
        except Exception, e:
            return self.log_and_raise(e, *args, **kwargs)

        return response

    def handle_error_no_active_tokens(self, e, *args, **kwargs):
        if self.used_access_tokens:
            # wait 1 sec and repeat with empty used_access_tokens
            self.logger.warning("Waiting 1 sec, because all active tokens are used, method: %s, recursion count: %d" %
                                (self.method, self.recursion_count))
            self.used_access_tokens = []
            return self.sleep_repeat_call(*args, **kwargs)
        else:
            self.logger.warning("Suddenly updating tokens, because no active access tokens and used_access_tokens "
                                "empty, method: %s, recursion count: %d" % (self.method, self.recursion_count))
            self.update_tokens()
            return self.repeat_call(*args, **kwargs)

    def handle_error_message(self, e, *args, **kwargs):
        # check if error message contains any of defined messages
        for message in self.sleep_repeat_error_messages:
            if message in str(e):
                return self.sleep_repeat_call(*args, **kwargs)
        return

    def handle_error_code(self, e, *args, **kwargs):
        # try to find method for handling exception by it's code
        try:
            return getattr(self, 'handle_error_code_%s' % self.get_error_code(e))(e, *args, **kwargs)
        except AttributeError:
            return self.log_and_raise(e, *args, **kwargs)

    def log_and_raise(self, e, *args, **kwargs):
        self.logger.error("Error '%s'. Method %s, args: %s, kwargs: %s, recursion count: %d" % (
            e, self.method, args, kwargs, self.recursion_count))
        error_class = type(e)
        raise error_class, e, sys.exc_info()[2]

    def get_error_code(self, e):
        return e.code

    def handle_error_repeat(self, e, *args, **kwargs):
        self.logger.error("Exception: '%s' registered while executing method %s with params %s, recursion count: %d"
                          % (e, self.method, kwargs, self.recursion_count))
        return self.sleep_repeat_call(*args, **kwargs)

    def sleep_repeat_call(self, *args, **kwargs):
        time.sleep(kwargs.pop('seconds', 1))
        return self.repeat_call(*args, **kwargs)

    def repeat_call(self, *args, **kwargs):
        self.recursion_count += 1
        if self.token_tag:
            kwargs[self.token_tag_arg_name] = self.token_tag
        if self.user:
            kwargs[self.user_arg_name] = self.user
        return self.call(self.method, *args, **kwargs)

    def update_tokens(self):
        lock_name = 'update_tokens_for_%s' % self.provider
        self.consistent_token = None
        try:
            # the first call of method will update tokens, all others will just wait for releasing the lock
            with distributedlock(lock_name, blocking=False):
                self.logger.info("Updating access tokens, method: %s, recursion count: %d" % (self.method,
                                                                                              self.recursion_count))
                AccessToken.objects.fetch(provider=self.provider)
                return True
        except LockNotAcquiredError:
            # wait until lock will be released and return
            updated = False
            while not updated:
                self.logger.info("Updating access tokens, waiting for another execution, method: %s, recursion "
                                 "count: %d" % (self.method, self.recursion_count))
                try:
                    with distributedlock(lock_name, blocking=False):
                        updated = True
                except LockNotAcquiredError:
                     time.sleep(1)
            return True
        except AccessTokenGettingError:
            if self.recursion_count <= self.update_tokens_max_count:
                time.sleep(1)
                self.recursion_count += 1
                self.update_tokens()
                return True
            else:
                raise

    def refresh_tokens(self):
        # TODO: implement the same logic of distributedlock as in update_tokens method
        if self.consistent_token:
            self.update_tokens()
        else:
            try:
                return AccessToken.objects.refresh(self.provider)
            except AccessTokenRefreshingError:
                if self.recursion_count <= self.refresh_tokens_max_count:
                    time.sleep(1)
                    self.recursion_count += 1
                    self.refresh_tokens()
                else:
                    raise

    def get_tokens(self, **kwargs):
        return AccessToken.objects.filter(provider=self.provider, **kwargs).order_by('-granted_at')

    def get_token(self, **kwargs):
        token = None

        if self.consistent_token not in self.used_access_tokens:
            token = self.consistent_token

        if not token:
            if self.user:
                # python social auth hook
                return self.get_token_for_user()

            tokens = self.get_tokens(**kwargs)

            if not tokens:
                self.update_tokens()
                tokens = self.get_tokens(**kwargs)

            if self.used_access_tokens:
                tokens = tokens.exclude(access_token__in=self.used_access_tokens)

            try:
                token = tokens[0].access_token
            except IndexError:
                raise NoActiveTokens("There is no active AccessTokens for provider %s with kwargs: %s, used_tokens: %s"
                                     % (self.provider, kwargs, self.used_access_tokens))

        return token

    @property
    def social_auth_provider(self):
        return NotImplementedError()

    def get_token_for_user(self):
        from social.apps.django_app.default.models import UserSocialAuth
        social_auth = UserSocialAuth.objects.get(user=self.user, provider=self.provider_social_auth)
        return social_auth.extra_data['access_token']

    def get_logger(self):
        return logging.getLogger('%s_api' % self.provider)

    @abstractproperty
    def provider(self):
        pass

    @abstractmethod
    def get_api(self, token):
        pass

    @abstractmethod
    def get_api_response(self):
        pass


class Singleton(ABCMeta):
    """
    Singleton metaclass for API classes
    from here http://stackoverflow.com/a/33201/87535
    """

    def __init__(cls, name, bases, dict):
        super(Singleton, cls).__init__(name, bases, dict)
        cls.instance = None

    def __call__(cls, *args, **kw):
        if cls.instance is None:
            cls.instance = super(Singleton, cls).__call__(*args, **kw)
        return cls.instance


def override_api_context(provider, **kwargs):
    return override_settings(OAUTH_TOKENS_API_CALL_CONTEXT={provider: kwargs})
