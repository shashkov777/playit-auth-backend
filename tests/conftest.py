import os
import pytest
import pytest_asyncio
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient, ASGITransport

from main import app
from src.db.db import Base, get_db_session

# --- Загрузка переменных окружения (если нужно, то поменяйте в .env файле URL тестовой базы данных) ---
load_dotenv()
TEST_DATABASE_PASSWORD = os.getenv("TEST_DATABASE_PASSWORD", "postgres")
TEST_DATABASE_NAME = os.getenv("TEST_DATABASE_NAME", "test_db")
TEST_DATABASE_USER = os.getenv("TEST_DATABASE_USER", "postgres")
TEST_DATABASE_HOST = os.getenv("TEST_DATABASE_HOST", "db_test")  # Хост внутри Docker сети
TEST_DATABASE_URL = f"postgresql://{TEST_DATABASE_USER}:{TEST_DATABASE_PASSWORD}@{TEST_DATABASE_HOST}:5432/{TEST_DATABASE_NAME}"

# --- Создаём синхронный engine и sessionmaker для тестовой БД ---
engine_test = create_engine(TEST_DATABASE_URL, future=True)
TestSession = sessionmaker(bind=engine_test, expire_on_commit=False)


@pytest.fixture(autouse=True)
def prepare_database():
    """
    Перед каждым тестом дропаем все таблицы и создаём заново,
    чтобы тесты были изолированными.
    """
    Base.metadata.drop_all(bind=engine_test)
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture
def override_get_db_session():
    """
    Переопределяет зависимость get_db_session,
    чтобы в тестах использовать тестовую (синхронную) БД.
    """

    def _override():
        with TestSession() as session:
            yield session

    # Устанавливаем переопределение
    app.dependency_overrides[get_db_session] = _override

    # После завершения теста убираем переопределение, чтобы не протекало в другие тесты
    yield
    app.dependency_overrides.pop(get_db_session, None)


@pytest_asyncio.fixture
async def client(override_get_db_session):
    """
    Создаём асинхронный клиент для тестирования FastAPI-приложения.
    Используем ASGITransport, чтобы тестировать эндпоинты в памяти (без реального http-сервера).
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
