from datasette import Forbidden
from datasette_plugin_router import Router
from functools import wraps

router = Router()

LIBFEC_ACCESS_NAME = "datasette_libfec_access"
LIBFEC_WRITE_NAME = "datasette_libfec_write"


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

