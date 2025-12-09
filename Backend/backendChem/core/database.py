from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from core.config_loader import settings

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ Tambahkan fungsi untuk create table
def init_db():
    from user.models.user import User  # pastikan model di-import
    from chem.models.generation import Generation  # pastikan model di-import
    Base.metadata.create_all(bind=engine)
