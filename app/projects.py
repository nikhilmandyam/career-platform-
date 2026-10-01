import logging

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.database import DatabaseConfigurationError, get_session_factory
from app.models import Project

logger = logging.getLogger(__name__)


def load_projects() -> list[Project] | None:
    try:
        with get_session_factory()() as session:
            statement = select(Project).order_by(
                Project.display_order,
                Project.id,
            )
            return list(session.scalars(statement))
    except (DatabaseConfigurationError, SQLAlchemyError):
        logger.exception("Failed to load projects")
        return None
