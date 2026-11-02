from python_tools import (
    MyLogger,
    NoInternetError,
    PasswordNotExists,
    PushoverKeysNotFound,
    PushoverNotificationFailed,
    Scraper,
    SiteChangedScraper,
    SiteTextChangedScraper,
    default_logger,
    email_errors,
    mail,
    push_notification,
)


def test_selected_symbols_are_available_at_package_level():
    assert callable(email_errors)
    assert callable(default_logger)
    assert callable(mail)
    assert callable(push_notification)
    assert MyLogger
    assert Scraper
    assert SiteChangedScraper
    assert SiteTextChangedScraper


def test_domain_exceptions_are_available_at_package_level():
    assert issubclass(NoInternetError, OSError)
    assert issubclass(PushoverKeysNotFound, Exception)
    assert issubclass(PushoverNotificationFailed, Exception)
    assert issubclass(PasswordNotExists, Exception)
