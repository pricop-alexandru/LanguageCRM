from collections.abc import Generator

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.identity import normalize_name

# Automatically creates the local crm.db file in the container/folder
SQLALCHEMY_DATABASE_URL = "sqlite:///./crm.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Client model skeleton - teammates can add new columns here
class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    phone = Column(String, unique=True, index=True, nullable=True)
    normalized_name = Column(String, index=True, nullable=True)

# Order model skeleton
class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    description = Column(String)
    status = Column(String, default="Noua")

def init_db():
    if inspect(engine).has_table("clients"):
        columns = {column["name"] for column in inspect(engine).get_columns("clients")}
        with engine.begin() as connection:
            if "phone" not in columns:
                connection.execute(text("ALTER TABLE clients ADD COLUMN phone VARCHAR"))
            if "normalized_name" not in columns:
                connection.execute(
                    text("ALTER TABLE clients ADD COLUMN normalized_name VARCHAR")
                )

    Base.metadata.create_all(bind=engine)
    with engine.begin() as connection:
        rows = connection.execute(
            text("SELECT id, name FROM clients WHERE normalized_name IS NULL")
        ).fetchall()
        for client_id, name in rows:
            normalized_name = normalize_name(name) if name else None
            connection.execute(
                text("UPDATE clients SET normalized_name = :name WHERE id = :id"),
                {"name": normalized_name, "id": client_id},
            )


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()