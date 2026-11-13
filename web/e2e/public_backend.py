"""Owned loopback-only native backend for public-mode browser verification."""

import argparse
import os
import shutil
from pathlib import Path

import uvicorn

from traceweaver.public_demo import PublicSettings, create_app

parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
output = Path(os.environ["TRACEWEAVER_PUBLIC_TEST_OUTPUT"])
bundle = output / "bundle"
shutil.copytree(root / "examples/judge-demo", bundle)
application = create_app(PublicSettings(bundle, (f"127.0.0.1:{args.port}",), allow_http=True))
uvicorn.run(
    application,
    host="127.0.0.1",
    port=args.port,
    workers=1,
    proxy_headers=False,
    forwarded_allow_ips="",
    access_log=False,
    server_header=False,
)
