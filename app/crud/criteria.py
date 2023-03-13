from app import models

from .base import BaseCRUD


class CriteriaCRUD(BaseCRUD[models.Criteria, models.CriteriaCreate, models.CriteriaUpdate]):
    pass


criteria = CriteriaCRUD(models.Criteria)
