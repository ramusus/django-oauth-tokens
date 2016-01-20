class LoginPasswordError(Exception):
    pass


class AccountLocked(Exception):
    pass


class WrongRedirectUrl(Exception):
    pass


class WrongAuthorizationResponseUrl(Exception):
    pass


class RedirectUriError(Exception):
    pass
