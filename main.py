from datetime import timedelta
from uuid import uuid4

from fastapi import Depends, FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.sessions import SessionMiddleware

from url_shortener.cache import redis_connection
from url_shortener.conf import config
from url_shortener.database import Base, LinkModel, engine, get_session
from url_shortener.scheduler import scheduler
from url_shortener.schema import UrlListSchema, UrlSchema, UserUrlsSchema
from url_shortener.utils import generate_subpart, url_for

app = FastAPI(debug=config.debug)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.middleware("http")
async def session_middleware(request: Request, call_next):
    if not request.session.get("id", None):
        request.session["id"] = str(uuid4())
    response = await call_next(request)
    session = request.cookies.get("session")
    if session:
        response.set_cookie(
            key="session", value=request.cookies.get("session"), httponly=True
        )
    return response


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    scheduler.add_job(
        LinkModel.remove_old_urls,
        "interval",
        minutes=config.cleanup_interval,
    )
    scheduler.start()


@app.on_event("shutdown")
async def shutdown():
    [job.remove() for job in scheduler.get_jobs()]
    scheduler.shutdown()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/s/", response_model=UserUrlsSchema)
async def list_short_urls(
    request: Request,
    page: int = Query(default=1, gt=0),
    limit: int = Query(default=10, lt=51),
    session: AsyncSession = Depends(get_session),
):
    user = request.session["id"]
    data, next_page, max_page = await LinkModel.list_paginated(
        session, user, page, limit
    )
    if next_page:
        next_page_url = url_for(
            app, "list_short_urls", query_params={"page": next_page, "limit": limit}
        )
    max_page_url = url_for(
        app, "list_short_urls", query_params={"page": max_page, "limit": limit}
    )
    return UserUrlsSchema(
        data=UrlListSchema.from_orm(data),
        page=page,
        limit=limit,
        next_page=next_page_url,
        max_page=max_page_url,
    )


@app.post("/s/", response_model=UrlSchema)
async def create_short_url(
    request: Request,
    url_data: UrlSchema,
    session: AsyncSession = Depends(get_session),
):
    if url_data.subpart:
        if await LinkModel.subpart_exists(session, url_data.subpart):
            return JSONResponse(
                content={
                    "message": "Subpart already used",
                    "invalid": "subpart",
                },
                status_code=403,
            )
    else:
        subpart = generate_subpart()
        while True:
            if not await LinkModel.subpart_exists(session, subpart):
                break
            subpart = generate_subpart()
        url_data.subpart = subpart

    await LinkModel.create(
        session, request.session["id"], url_data.subpart, url_data.url
    )
    await session.commit()
    return url_data


@app.get("/s/{subpart}/", response_class=RedirectResponse)
async def url_redirect(
    request: Request,
    subpart: str,
    session: AsyncSession = Depends(get_session),
):
    if url := redis_connection.get(subpart):
        url = url.decode()
    else:
        obj = await LinkModel.get_url(session, subpart)
        if not obj:
            return templates.TemplateResponse(
                "404.html",
                {"request": request},
            )
        url = obj.url
        redis_connection.set(
            subpart, url, ex=timedelta(minutes=config.cleanup_interval)
        )
    return RedirectResponse(url)


app.add_middleware(SessionMiddleware, secret_key=config.secret_key)
