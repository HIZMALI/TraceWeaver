"""Serve only built console assets on the existing local application origin."""

from importlib.resources import files

from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles


def mount_console(application):
    directory = files("traceweaver").joinpath("web_static")
    application.mount(
        "/assets",
        StaticFiles(directory=str(directory.joinpath("assets")), check_dir=False),
        name="console-assets",
    )

    @application.get("/", include_in_schema=False)
    def console_index():
        path = directory.joinpath("index.html")
        if not path.is_file():
            return HTMLResponse(
                "<h1>TraceWeaver console build unavailable</h1>"
                "<p>Build the local web package as documented in README.</p>",
                status_code=503,
            )
        return FileResponse(
            str(path),
            media_type="text/html",
            headers={
                "Cache-Control": "no-cache",
                "X-Content-Type-Options": "nosniff",
                "Referrer-Policy": "no-referrer",
                "Content-Security-Policy": "default-src 'self'; script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
                "connect-src 'self'; font-src 'self'; object-src 'none'; "
                "base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
            },
        )
