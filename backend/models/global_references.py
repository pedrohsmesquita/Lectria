"""
GlobalReferences Model - Bibliography references with global numbering per book
"""
from sqlalchemy import Column, String, Integer, Text, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship
import uuid

from database import Base


class GlobalReferences(Base):
    __tablename__ = "global_references"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    reference_key = Column(String, nullable=False)  # Ex: "REF:SILVA_2022"
    reference_number = Column(Integer, nullable=False)  # Sequential numbering: 1, 2, 3...
    full_reference_abnt = Column(Text, nullable=False)  # ABNT formatted reference text
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationship to Books (many-to-one)
    book = relationship("Books", back_populates="global_references")

    # Relationship to Sections (many-to-many through section_references)
    sections = relationship(
        "Sections",
        secondary="section_references",
        back_populates="references"
    )

    # Constraints: ensure unique keys and numbers per book
    __table_args__ = (
        UniqueConstraint('book_id', 'reference_key', name='uq_book_reference_key'),
        UniqueConstraint('book_id', 'reference_number', name='uq_book_reference_number'),
    )

    def __repr__(self):
        return f"<GlobalReferences(id={self.id}, key={self.reference_key}, number={self.reference_number})>"
