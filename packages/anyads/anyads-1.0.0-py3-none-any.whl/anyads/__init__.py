# src/anyads/__init__.py

from .client import AnyAdsSDK, init, get_sdk_instance
from .exceptions import AnyAdsException, InitializationError, APIError


__all__ = [
    "AnyAdsSDK",
    "init",
    "get_sdk_instance",
    "AnyAdsException",
    "InitializationError",
    "APIError",
]

import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())