from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker

# Creeaza automat fisierul local crm.db in container/folder
SQLALCHEMY_DATABASE_URL = "sqlite:///./crm.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Schelet model Client - colegii pot adauga coloane noi aici
class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=True)

# Schelet model Comanda (Order)
class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    description = Column(String)
    status = Column(String, default="Noua")

def init_db():
    Base.metadata.create_all(bind=engine)