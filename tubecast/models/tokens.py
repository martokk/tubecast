from sqlmodel import SQLModel


class Tokens(SQLModel):
    access_token: str | None = None
    refresh_token: str | None = None


class TokenPayload(SQLModel):
    sub: str | None = None
