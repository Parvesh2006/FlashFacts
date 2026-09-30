from datetime import datetime, timezone
import json
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


class GeographicLocation(Base):
    __tablename__ = "geographic_locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    normalized_name = Column(String(255), nullable=False, index=True)
    location_type = Column(String(50), nullable=False, index=True)  # WORLD, COUNTRY, STATE, DISTRICT, CITY, etc.
    parent_id = Column(Integer, ForeignKey("geographic_locations.id"), nullable=True, index=True)
    country_code = Column(String(10), nullable=True, index=True)
    state_code = Column(String(10), nullable=True, index=True)
    district_code = Column(String(20), nullable=True, index=True)
    aliases_json = Column(Text, nullable=True, default="[]")  # JSON array string
    active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    parent = relationship("GeographicLocation", remote_side=[id], backref="children")
    event_locations = relationship("EventLocation", back_populates="location", cascade="all, delete-orphan")

    @property
    def aliases(self):
        if not self.aliases_json:
            return []
        try:
            return json.loads(self.aliases_json)
        except Exception:
            return []

    @aliases.setter
    def aliases(self, val):
        self.aliases_json = json.dumps(val or [])


class EventLocation(Base):
    __tablename__ = "event_locations"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    location_id = Column(Integer, ForeignKey("geographic_locations.id"), nullable=False, index=True)
    relation_type = Column(String(50), nullable=False, default="PRIMARY", index=True)  # PRIMARY, AFFECTED, MENTIONED
    confidence = Column(Float, nullable=False, default=1.0)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    event = relationship("Event", back_populates="event_locations")
    location = relationship("GeographicLocation", back_populates="event_locations")


Index("ix_event_locations_event_loc", EventLocation.event_id, EventLocation.location_id, unique=True)

