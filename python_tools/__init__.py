from .email_errors import NoInternetError, email_errors
from .my_logger import MyLogger, default_logger
from .notify import (
    PasswordNotExists,
    PushoverKeysNotFound,
    PushoverNotificationFailed,
    mail,
    push_notification,
)

__all__ = [
    "email_errors",
    "NoInternetError",
    "MyLogger",
    "default_logger",
    "mail",
    "push_notification",
    "PushoverKeysNotFound",
    "PushoverNotificationFailed",
    "PasswordNotExists",
    "Scraper",
    "SiteChangedScraper",
    "SiteTextChangedScraper",
]


def __getattr__(name):
    if name in {"Scraper", "SiteChangedScraper", "SiteTextChangedScraper"}:
        from .scraper import Scraper, SiteChangedScraper, SiteTextChangedScraper

        return {
            "Scraper": Scraper,
            "SiteChangedScraper": SiteChangedScraper,
            "SiteTextChangedScraper": SiteTextChangedScraper,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
