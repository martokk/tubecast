from sqlmodel import Session

from python_fastapi_stack import models
from python_fastapi_stack.core import security

from .base import BaseCRUD


class UserCRUD(BaseCRUD[models.User, models.UserCreate, models.UserUpdate]):
    async def create_with_password(
        self, db: Session, *, obj_in: models.UserCreateWithPassword
    ) -> models.User:
        """
        Create a new user by generating a hashed password from the provided password.

        Args:
            db (Session): The database session.
            obj_in (models.UserCreateWithPassword): The user to create.

        Returns:
            models.User: The created user.
        """
        obj_in_data = obj_in.dict(exclude_unset=True)
        obj_in_data["hashed_password"] = security.get_password_hash(obj_in_data["password"])
        del obj_in_data["password"]

        out_obj = models.UserCreate(**obj_in_data)
        return await self.create(db, obj_in=out_obj)

    async def authenticate(
        self, db: Session, *, username: str, password: str
    ) -> models.User | None:
        """
        Authenticate a user by checking the provided password against the hashed password.

        Args:
            db (Session): The database session.
            username (str): The username to authenticate.
            password (str): The password to authenticate.

        Returns:
            models.User | None: The authenticated user or None if the user does not exist or
                the password is incorrect.
        """
        _user = await self.get_or_none(db, username=username)
        if not _user:
            return None
        if not security.verify_password(
            plain_password=password, hashed_password=_user.hashed_password
        ):
            return None
        return _user

    def is_active(self, _user: models.User) -> bool:
        return _user.is_active

    def is_superuser(self, *, user_: models.User) -> bool:
        return user_.is_superuser


user = UserCRUD(model=models.User)
