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


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(String, primary_key=True, index=True)
    model = Column(String, nullable=False)
    prompt = Column(String, nullable=False)
    system_prompt = Column(String, nullable=True)
    tool_calls = Column(String, nullable=True)
    tool_results = Column(String, nullable=True)
    output = Column(String, nullable=True)
    latency_ms = Column(Float, nullable=False, default=0.0)
    tokens_used = Column(Integer, nullable=True, default=0)
    source = Column(String, default="gemma")  # "gemma" or "fallback"
    status = Column(String, default="SUCCESS")  # "SUCCESS", "FALLBACK", "ERROR"
    created_at = Column(String, default=lambda: datetime.now().isoformat())


class AgentCache(Base):
    __tablename__ = "agent_cache"

    cache_key = Column(String, primary_key=True, index=True)
    model = Column(String, nullable=False)
    response = Column(String, nullable=False)
    created_at = Column(String, default=lambda: datetime.now().isoformat())


class AgentDecision(Base):
    """Stores human-in-the-loop controller approval/rejection of AI dispatch recommendations."""
    __tablename__ = "agent_decisions"

    id = Column(String, primary_key=True, index=True)
    run_id = Column(String, nullable=False, index=True)
    status = Column(String, default="PENDING")  # PENDING, APPROVED, REJECTED, EDITED
    controller_id = Column(String, nullable=True)
    edited_order = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    decided_at = Column(String, nullable=True)
    created_at = Column(String, default=lambda: datetime.now().isoformat())
