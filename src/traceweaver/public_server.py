"""One-worker public-demo launcher; local judge bindings remain unchanged."""

import os

import uvicorn


def main():
    value = os.environ.get("PORT", "10000")
    if not value.isascii() or not value.isdecimal() or not 1024 <= int(value) <= 65535:
        raise SystemExit("Invalid public service port")
    uvicorn.run(
        "traceweaver.public_demo:app",
        host="0.0.0.0",
        port=int(value),
        workers=1,
        proxy_headers=False,
        forwarded_allow_ips="",
        server_header=False,
        access_log=False,
        ws="none",
        limit_concurrency=24,
        backlog=64,
        timeout_keep_alive=3,
        timeout_graceful_shutdown=10,
    )


if __name__ == "__main__":
    main()
