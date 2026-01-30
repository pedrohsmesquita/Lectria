"""
UserAuth Model - Authentication credentials
"""
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from database import Base


class UserAuth(Base):
    __tablename__ = "user_auth"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship to UserProfiles (one-to-one)
    profile = relationship("UserProfiles", back_populates="user_auth", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<UserAuth(id={self.id}, email={self.email})>"
