import yaml
from sqlmodel import Session

from app import crud
from app.paths import SOURCES_EXPORT_FILE


async def export_sources(db: Session) -> None:
    """
    Export sources to a yaml file.

    Args:
        db (Session): Database session.
    """

    sources = await crud.source.get_all(db=db)

    output = []
    for source in sources:
        source_output = {
            "url": source.url,
            "created_by": source.created_by,
        }
        output.append(source_output)

    SOURCES_EXPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    yaml.safe_dump(
        output, SOURCES_EXPORT_FILE.open("w"), default_flow_style=False, allow_unicode=True
    )


async def import_sources(db: Session) -> None:
    """
    Import sources from a yaml file. create Source from url and created_by

    Args:
        db (Session): Database session.
    """
    sources = yaml.safe_load(SOURCES_EXPORT_FILE.open("r"))

    for source in sources:
        try:
            await crud.source.create_source_from_url(
                db=db, url=source["url"], user_id=source["created_by"]
            )
        except crud.RecordAlreadyExistsError:
            pass
