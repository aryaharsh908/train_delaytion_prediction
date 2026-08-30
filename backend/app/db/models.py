from sqlalchemy import Column, Integer, String, Float, Index, DateTime
from datetime import datetime
from app.db.database import Base

class CollectionJob(Base):
    __tablename__ = "collection_jobs"

    job_id = Column(String, primary_key=True, index=True)
    train_number = Column(String, index=True, nullable=False)
    start_date = Column(String, nullable=False)
    end_date = Column(String, nullable=False)
    current_date = Column(String, nullable=False)
    status = Column(String, default="PENDING", index=True)  # PENDING, RUNNING, COMPLETED, FAILED, PAUSED
    records_downloaded = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)
    last_successful_date = Column(String, nullable=True)
    created_at = Column(String, default=lambda: datetime.now().isoformat())
    updated_at = Column(String, default=lambda: datetime.now().isoformat(), onupdate=lambda: datetime.now().isoformat())


class HistoricalTrainRun(Base):
    __tablename__ = "historical_train_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    train_number = Column(String, nullable=False, index=True)
    train_name = Column(String, nullable=True)
    train_type = Column(String, nullable=True)
    journey_date = Column(String, nullable=False, index=True)
    station_sequence = Column(Integer, nullable=False)
    station_code = Column(String, nullable=False, index=True)
    station_name = Column(String, nullable=False)
    
    scheduled_arrival = Column(String, nullable=True)
    actual_arrival = Column(String, nullable=True)
    scheduled_departure = Column(String, nullable=True)
    actual_departure = Column(String, nullable=True)

    arrival_delay_minutes = Column(Float, nullable=True)
    departure_delay_minutes = Column(Float, nullable=True)

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    distance_from_origin = Column(Float, nullable=True)
    distance_to_destination = Column(Float, nullable=True)
    section_id = Column(String, nullable=True)

    source = Column(String, default="unknown")
    created_at = Column(String, default=lambda: datetime.now().isoformat())

    __table_args__ = (
        Index("idx_train_date", "train_number", "journey_date"),
        Index("idx_train_seq", "train_number", "station_sequence"),
        Index("idx_station_date", "station_code", "journey_date"),
    )
