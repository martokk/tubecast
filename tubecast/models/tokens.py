from sqlmodel import SQLModel


class Tokens(SQLModel):
    access_token: str
    refresh_token: str


class TokenPayload(SQLModel):
    sub: str | None = None
