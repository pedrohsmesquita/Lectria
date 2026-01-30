"""
UserProfiles Model - User personal information
"""
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base


class UserProfiles(Base):
    __tablename__ = "user_profiles"

    # user_auth_id is both PK and FK
    user_auth_id = Column(UUID(as_uuid=True), ForeignKey("user_auth.id", ondelete="CASCADE"), primary_key=True)
    full_name = Column(String, nullable=False)

    # Relationship to UserAuth (one-to-one)
    user_auth = relationship("UserAuth", back_populates="profile")

    # Relationship to Books (one-to-many)
    books = relationship("Books", back_populates="author_profile", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<UserProfiles(user_auth_id={self.user_auth_id}, full_name={self.full_name})>"
