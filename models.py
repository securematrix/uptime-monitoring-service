from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Monitor(Base):
    __tablename__ = 'monitors'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    method = Column(String(10), default='GET') # GET or HEAD
    frequency = Column(Integer, default=60) # in seconds
    timeout = Column(Float, default=10.0)
    
    # Alert configurations
    alert_threshold_consecutive_drops = Column(Integer, default=3)
    alert_response_time_threshold = Column(Float, default=2000.0) # in ms
    alert_email = Column(String(200), nullable=True)
    alert_webhook = Column(String(500), nullable=True)
    
    # State tracking
    is_paused = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    logs = relationship("MonitorLog", back_populates="monitor", cascade="all, delete-orphan")

class MonitorLog(Base):
    __tablename__ = 'monitor_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    monitor_id = Column(Integer, ForeignKey('monitors.id'), nullable=False)
    
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    status_code = Column(Integer, nullable=True)
    response_time = Column(Float, nullable=True) # in ms
    ttfb = Column(Float, nullable=True) # in ms
    
    is_success = Column(Boolean, default=False)
    error_message = Column(String(500), nullable=True)
    
    monitor = relationship("Monitor", back_populates="logs")
