import uuid
from sqlalchemy import UUID, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from core.db.db_config import Base


class Dustbin(Base):
    __tablename__ = "dustbins"

    id : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid7)

    name : Mapped[str] = mapped_column(String(150), nullable=False)

    latitude : Mapped[float] = mapped_column(Float, nullable=False)
    longitude : Mapped[float] = mapped_column(Float, nullable=False)

    address : Mapped[str] = mapped_column(Text, nullable=False)

    photos_keys : Mapped[list[str]] = mapped_column(JSONB, nullable=False)

    # Current reported condition
    fill_level : Mapped[String] = mapped_column(String, nullable=True)

    # Confidence that this bin actually exists and its data is correct
    confidence_score : Mapped[float] = mapped_column(Float, default=50.0, nullable=False)

    # Number of people who have reported on the status of dustbin
    report_count : Mapped[int] = mapped_column(Integer, default=1)

    # Last timestamp of when the dustbin's existence was verified
    last_verified_at = mapped_column(DateTime(timezone=True), nullable=True)

    created_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )