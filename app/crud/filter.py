from app import models

from .base import BaseCRUD


class FilterCRUD(BaseCRUD[models.Filter, models.FilterCreate, models.FilterUpdate]):
    pass


filter = FilterCRUD(models.Filter)
