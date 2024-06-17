from aiohttp.web import HTTPFound, middleware, HTTPException

from modules.application import PMRequest, PMApplication

async def handle_404(request: PMRequest):
    # FixMe check what user want to get if file then return 404
    return HTTPFound('/projects/')


async def handle_500(request: PMRequest):
    return HTTPFound('/projects/')


def create_error_middleware(overrides):

    @middleware
    async def error_middleware(request, handler):
        try:
            return await handler(request)
        except HTTPException as ex:
            override = overrides.get(ex.status)
            if override:
                return await override(request)

            raise
        except Exception:
            request.protocol.logger.exception("Error handling request")
            return await overrides[500](request)

    return error_middleware

def setup_middlewares(app: PMApplication):
    error_middlewares = create_error_middleware({
        404: handle_404,
        500: handle_500,
    })
    app.middlewares.append(error_middlewares)