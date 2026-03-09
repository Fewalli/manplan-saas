from collections.abc import Generator
from typing import TypedDict

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token, get_password_hash
from app.db.session import get_db
from app.models import Base
from app.models.area import Area
from app.models.asset import Asset
from app.models.role import Role, UserRole
from app.models.tenant import Tenant
from app.models.user import User
from manplan_api.main import app



class SeededDb(TypedDict):
    tenant: Tenant
    admin_user: User
    technician_user: User
    requester_user: User
    multi_role_user: User
    area: Area
    asset: Asset
    


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        class_=Session,
    )

    Base.metadata.create_all(bind=engine)

    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def seeded_db(db_session: Session) -> SeededDb:
    tenant = Tenant(name="Tenant Teste", slug="tenant-teste", is_active=True)
    db_session.add(tenant)
    db_session.flush()

    admin_role = Role(tenant_id=tenant.id, code="admin_tenant", name="Admin do Tenant", is_active=True)
    technician_role = Role(tenant_id=tenant.id, code="tecnico", name="Técnico", is_active=True)
    planner_role = Role(tenant_id=tenant.id, code="planejador", name="Planejador", is_active=True)
    requester_role = Role(tenant_id=tenant.id, code="solicitante", name="Solicitante", is_active=True)

    db_session.add_all([admin_role, technician_role, planner_role, requester_role])
    db_session.flush()

    admin_user = User(
        tenant_id=tenant.id,
        full_name="Admin Teste",
        email="admin@teste.com",
        password_hash=get_password_hash("Senha123!"),
        is_active=True,
    )
    technician_user = User(
        tenant_id=tenant.id,
        full_name="Tecnico Teste",
        email="tecnico@teste.com",
        password_hash=get_password_hash("Senha123!"),
        is_active=True,
    )
    requester_user = User(
        tenant_id=tenant.id,
        full_name="Solicitante Teste",
        email="solicitante@teste.com",
        password_hash=get_password_hash("Senha123!"),
        is_active=True,
    )
    multi_role_user = User(
        tenant_id=tenant.id,
        full_name="Multiplo Papel",
        email="multiplo@teste.com",
        password_hash=get_password_hash("Senha123!"),
        is_active=True,
    )

    db_session.add_all([admin_user, technician_user, requester_user, multi_role_user])
    db_session.flush()

    db_session.add_all(
        [
            UserRole(user_id=admin_user.id, role_id=admin_role.id),
            UserRole(user_id=technician_user.id, role_id=technician_role.id),
            UserRole(user_id=requester_user.id, role_id=requester_role.id),
            UserRole(user_id=multi_role_user.id, role_id=admin_role.id),
            UserRole(user_id=multi_role_user.id, role_id=planner_role.id),
        ]
    )
    db_session.flush()

    area = Area(
        tenant_id=tenant.id,
        code="AREA-01",
        name="Área Teste",
        is_active=True,
    )
    db_session.add(area)
    db_session.flush()

    asset = Asset(
        tenant_id=tenant.id,
        area_id=area.id,
        code="ATV-001",
        name="Máquina Teste",
        location="Linha 1",
        is_active=True,
    )
    db_session.add(asset)
    db_session.commit()

    return {
        "tenant": tenant,
        "admin_user": admin_user,
        "technician_user": technician_user,
        "requester_user": requester_user,
        "multi_role_user": multi_role_user,
        "area": area,
        "asset": asset,
    }


@pytest.fixture()
def client(
    db_session: Session,
    seeded_db: SeededDb,
) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def admin_token(seeded_db: SeededDb) -> str:
    admin_user = seeded_db["multi_role_user"]
    tenant = seeded_db["tenant"]
    return create_access_token(subject=admin_user.email, tenant_id=tenant.id)


@pytest.fixture()
def technician_token(seeded_db: SeededDb) -> str:
    technician_user = seeded_db["technician_user"]
    tenant = seeded_db["tenant"]
    return create_access_token(subject=technician_user.email, tenant_id=tenant.id)


@pytest.fixture()
def requester_token(seeded_db: SeededDb) -> str:
    requester_user = seeded_db["requester_user"]
    tenant = seeded_db["tenant"]
    return create_access_token(subject=requester_user.email, tenant_id=tenant.id)