from re import compile

from pydantic import BaseModel, validator

url_regexp = compile(
    r"(?P<schema>http(s)?:\/\/)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)"
)


class UrlSchema(BaseModel):
    url: str
    subpart: str | None = ""

    class Config:
        orm_mode = True

    @validator("url")
    def url_validator(cls, v: str):
        result = url_regexp.match(v)
        if not result:
            raise ValueError("Incorrect url")
        elif not result.groupdict().get("schema"):
            v = f"https://{v}"
        return v


class UrlListSchema(BaseModel):
    __root__: list[UrlSchema]

    class Config:
        orm_mode = True


class UserUrlsSchema(BaseModel):
    data: UrlListSchema
    page: int
    limit: int
    next_page: str | None = None
    max_page: str
