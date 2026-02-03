from datasette import Forbidden
from datasette_plugin_router import Router
from functools import wraps

router = Router()

LIBFEC_ACCESS_NAME = "datasette_libfec_access"

# decorator for routes, to ensure the proper permissions are checked
def check_permission():
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

