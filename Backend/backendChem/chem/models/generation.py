# chem/models/generation.py
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Float,
    ForeignKey,
    DateTime,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func



from core.database import Base


class Generation(Base):
    __tablename__ = "generations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))

    smi_string = Column(String, nullable=False)
    num_molecules = Column(Integer, nullable=False)
    algorithm = Column(String, nullable=False)
    property_to_optimize = Column(String, nullable=False)
    min_similarity = Column(Float, nullable=False)
    particles = Column(Integer, nullable=False)
    iterations = Column(Integer, nullable=False)
    minimize = Column(Boolean, nullable=False)

    result = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    
