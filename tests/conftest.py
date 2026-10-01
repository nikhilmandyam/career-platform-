import pytest


@pytest.fixture
def database_url(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'test.db'}"
    monkeypatch.setenv("DATABASE_URL", url)

    try:
        from app.database import build_engine, get_session_factory
        from app.models import Base
    except ModuleNotFoundError as error:
        if error.name not in {"app.database", "app.models"}:
            raise
        yield url
        return

    get_session_factory.cache_clear()
    engine = build_engine(url)
    Base.metadata.create_all(engine)
    yield url
    get_session_factory.cache_clear()
    engine.dispose()
