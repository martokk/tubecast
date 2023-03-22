from sqlmodel import Session

from app import crud, models
from app.models import Filter, Source


async def test_filter_videos(
    db: Session,
    source_1_w_videos: Source,
    filter_1: Filter,
    normal_user: models.User,
) -> None:
    assert len(source_1_w_videos.videos) == 2
    filtered_videos = filter_1.videos()
    assert len(filtered_videos) == 2

    # Add criterias
    criteria = models.CriteriaCreate(
        **{
            "field": models.CriteriaField.KEYWORD.value,
            "operator": models.CriteriaOperator.MUST_CONTAIN.value,
            "value": source_1_w_videos.videos[0].title,
            "unit_of_measure": models.CriteriaUnitOfMeasure.KEYWORD.value,
            "filter_id": filter_1.id,
            "created_by": normal_user.id,
        }
    )
    await crud.criteria.create(db=db, obj_in=criteria)

    filtered_videos = filter_1.videos()
    assert len(filtered_videos) == 1
