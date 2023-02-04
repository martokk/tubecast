from sqlmodel import SQLModel


class HealthCheck(SQLModel):
    name: str
    version: str
    description: str
