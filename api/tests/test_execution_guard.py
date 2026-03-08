from collections.abc import Generator
from datetime import datetime, timezone

import pytest
from sqlalchemy import Column, DateTime, Integer, MetaData, Table, create_engine
from sqlalchemy.orm import Session

from app.services.execution_guard import assert_technician_has_no_active_execution


metadata = MetaData()

execution_sessions = Table(
    "execution_sessions",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("tenant_id", Integer, nullable=False),
    Column("work_order_id", Integer, nullable=False),
    Column("technician_id", Integer, nullable=False),
    Column("started_at", DateTime(timezone=True), nullable=False),
    Column("ended_at", DateTime(timezone=True), nullable=True),
)


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    metadata.drop_all(engine)
    engine.dispose()


def test_allows_when_technician_has_no_active_execution(db: Session) -> None:
    assert_technician_has_no_active_execution(
        db,
        tenant_id=1,
        technician_user_id=100,
    )


def test_blocks_when_technician_has_active_execution(db: Session) -> None:
    db.execute(
        execution_sessions.insert().values(
            tenant_id=1,
            work_order_id=200,
            technician_id=100,
            started_at=datetime.now(timezone.utc),
            ended_at=None,
        )
    )
    db.commit()

    with pytest.raises(ValueError):
        assert_technician_has_no_active_execution(
            db,
            tenant_id=1,
            technician_user_id=100,
        )