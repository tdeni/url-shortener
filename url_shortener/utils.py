import string
from random import choices

from fastapi import FastAPI

printable = string.ascii_letters + string.digits + "#$%&_-()[]+=,*"


def generate_subpart(ln: int = 5) -> str:
    return "".join(choices(printable, k=ln))


def url_for(
    app: FastAPI,
    name: str,
    path_params: dict | None = None,
    query_params: dict | None = None,
) -> str:
    path_params = path_params or {}
    path = app.url_path_for(name, **path_params)
    if query_params:
        path += "?" + "&".join(f"{k}={v}" for k, v in query_params.items())
    return path
