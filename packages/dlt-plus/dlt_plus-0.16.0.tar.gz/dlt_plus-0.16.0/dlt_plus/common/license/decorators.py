from functools import wraps
from typing import Any, Callable, Union

from dlt.common.typing import TFun

from dlt_plus.common.constants import LICENSE_PUBLIC_KEY

from .license import (
    validate_license,
    discover_license,
    ensure_scope,
    get_scopes,
    ensure_feature_scope,
)

from .license import DltLicenseException, DltUnknownScopeException

# save the scopes that were already extracted from a valid license
# to avoid validating the license multiple times
_VALIDATED_SCOPES: Union[list[str], None] = None


def ensure_license_with_scope(scope: str) -> None:
    """Ensures that license with `scope` is available and validates dlt-plus
    public key LICENSE_PUBLIC_KEY
    """
    global _VALIDATED_SCOPES

    if _VALIDATED_SCOPES is None:
        license_string = discover_license()
        license = validate_license(LICENSE_PUBLIC_KEY, license_string)
        _VALIDATED_SCOPES = get_scopes(license)

    ensure_scope(_VALIDATED_SCOPES, scope)


def is_scope_active(scope: str) -> bool:
    """Checks if a scope is currently active, if there is a missing license or an invalid license,
    returns False without raising an exception.
    """
    try:
        ensure_license_with_scope(scope)
        return True
    except DltUnknownScopeException:
        # this is a dlt developer error, raise here
        raise
    except DltLicenseException:
        return False


def require_license(scope: str) -> Callable[[TFun], TFun]:
    """Decorator that requires a valid license to execute the decorated function.

    Args:
        scope (str): The scope of the license required to execute the function.
            It is always a feature scope in form package.feature ie. `dlt_plus.sources.mssql`

    Returns:
        TFun: A decorator function that validates the license before executing the function.

    Raises:
        DltLicenseNotFoundException: If no license is found in environment or secrets.toml
        DltLicenseExpiredException: If the license has expired
        DltLicenseSignatureInvalidException: If the license signature is invalid
    """
    ensure_feature_scope(scope)

    def decorator(func: TFun) -> TFun:
        @wraps(func)
        def wrapper_func(*args: Any, **kwargs: Any) -> Any:
            ensure_license_with_scope(scope)
            return func(*args, **kwargs)

        return wrapper_func  # type: ignore[return-value]

    return decorator
