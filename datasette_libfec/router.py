from datasette import Forbidden
from datasette_plugin_router import Router
from functools import wraps

router = Router()

LIBFEC_ACCESS_NAME = "datasette_libfec_access"
LIBFEC_WRITE_NAME = "datasette_libfec_write"


async def check_alerts_available(datasette, actor) -> bool:
    """Check if datasette-alerts is installed and the actor has alerts permission."""
    try:
        from datasette_alerts import ALERTS_ACCESS_NAME  # type: ignore[import-not-found]

        return await datasette.allowed(action=ALERTS_ACCESS_NAME, actor=actor)
    except ImportError:
        return False


def check_permission():
    """Decorator for routes requiring read access."""

    def decorator(func):
        @wraps(func)
        async def wrapper(datasette, request, **kwargs):
            result = await datasette.allowed(
                action=LIBFEC_ACCESS_NAME, actor=request.actor
            )
            if not result:
                raise Forbidden("Permission denied for datasette-libfec access")
            return await func(datasette=datasette, request=request, **kwargs)

        return wrapper

    return decorator


def check_write_permission():
    """Decorator for routes requiring write access (import, RSS, etc.)."""

    def decorator(func):
        @wraps(func)
        async def wrapper(datasette, request, **kwargs):
            # Check read access first
            read_allowed = await datasette.allowed(
                action=LIBFEC_ACCESS_NAME, actor=request.actor
            )
            if not read_allowed:
                raise Forbidden("Permission denied for datasette-libfec access")

            # Check write access
            write_allowed = await datasette.allowed(
                action=LIBFEC_WRITE_NAME, actor=request.actor
            )
            if not write_allowed:
                raise Forbidden("Permission denied for datasette-libfec write access")

            return await func(datasette=datasette, request=request, **kwargs)

        return wrapper

    return decorator
