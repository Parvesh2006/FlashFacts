"""
Geographic Location Service & Location Extractor.
"""
import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple, Set

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.location import GeographicLocation, EventLocation
from app.models.event import Event
from app.models.source import Source

logger = logging.getLogger("app")

# Standard reference locations seed definition covering All 28 Indian States & Key Cities/UTs
REFERENCE_LOCATIONS = [
    {
        "name": "World",
        "normalized_name": "world",
        "location_type": "WORLD",
        "country_code": "GLOBAL",
        "aliases": ["Global", "International", "Earth"],
    },
    {
        "name": "India",
        "normalized_name": "india",
        "location_type": "COUNTRY",
        "country_code": "IN",
        "parent": "World",
        "aliases": ["Republic of India", "IN", "Bharat", "Indian Government", "Government of India", "Union Government"],
    },
    # 28 Indian States
    {"name": "Andhra Pradesh", "normalized_name": "andhra pradesh", "location_type": "STATE", "country_code": "IN", "state_code": "AP", "parent": "India", "aliases": ["AP"]},
    {"name": "Arunachal Pradesh", "normalized_name": "arunachal pradesh", "location_type": "STATE", "country_code": "IN", "state_code": "AR", "parent": "India", "aliases": ["AR"]},
    {"name": "Assam", "normalized_name": "assam", "location_type": "STATE", "country_code": "IN", "state_code": "AS", "parent": "India", "aliases": ["AS"]},
    {"name": "Bihar", "normalized_name": "bihar", "location_type": "STATE", "country_code": "IN", "state_code": "BR", "parent": "India", "aliases": ["BR"]},
    {"name": "Chhattisgarh", "normalized_name": "chhattisgarh", "location_type": "STATE", "country_code": "IN", "state_code": "CG", "parent": "India", "aliases": ["CG"]},
    {"name": "Goa", "normalized_name": "goa", "location_type": "STATE", "country_code": "IN", "state_code": "GA", "parent": "India", "aliases": ["GA"]},
    {"name": "Gujarat", "normalized_name": "gujarat", "location_type": "STATE", "country_code": "IN", "state_code": "GJ", "parent": "India", "aliases": ["GJ"]},
    {"name": "Haryana", "normalized_name": "haryana", "location_type": "STATE", "country_code": "IN", "state_code": "HR", "parent": "India", "aliases": ["HR"]},
    {"name": "Himachal Pradesh", "normalized_name": "himachal pradesh", "location_type": "STATE", "country_code": "IN", "state_code": "HP", "parent": "India", "aliases": ["HP"]},
    {"name": "Jharkhand", "normalized_name": "jharkhand", "location_type": "STATE", "country_code": "IN", "state_code": "JH", "parent": "India", "aliases": ["JH"]},
    {"name": "Karnataka", "normalized_name": "karnataka", "location_type": "STATE", "country_code": "IN", "state_code": "KA", "parent": "India", "aliases": ["KA"]},
    {"name": "Kerala", "normalized_name": "kerala", "location_type": "STATE", "country_code": "IN", "state_code": "KL", "parent": "India", "aliases": ["KL"]},
    {"name": "Madhya Pradesh", "normalized_name": "madhya pradesh", "location_type": "STATE", "country_code": "IN", "state_code": "MP", "parent": "India", "aliases": ["MP"]},
    {"name": "Maharashtra", "normalized_name": "maharashtra", "location_type": "STATE", "country_code": "IN", "state_code": "MH", "parent": "India", "aliases": ["MH"]},
    {"name": "Manipur", "normalized_name": "manipur", "location_type": "STATE", "country_code": "IN", "state_code": "MN", "parent": "India", "aliases": ["MN"]},
    {"name": "Meghalaya", "normalized_name": "meghalaya", "location_type": "STATE", "country_code": "IN", "state_code": "ML", "parent": "India", "aliases": ["ML"]},
    {"name": "Mizoram", "normalized_name": "mizoram", "location_type": "STATE", "country_code": "IN", "state_code": "MZ", "parent": "India", "aliases": ["MZ"]},
    {"name": "Nagaland", "normalized_name": "nagaland", "location_type": "STATE", "country_code": "IN", "state_code": "NL", "parent": "India", "aliases": ["NL"]},
    {"name": "Odisha", "normalized_name": "odisha", "location_type": "STATE", "country_code": "IN", "state_code": "OR", "parent": "India", "aliases": ["OR", "Orissa"]},
    {"name": "Punjab", "normalized_name": "punjab", "location_type": "STATE", "country_code": "IN", "state_code": "PB", "parent": "India", "aliases": ["PB"]},
    {"name": "Rajasthan", "normalized_name": "rajasthan", "location_type": "STATE", "country_code": "IN", "state_code": "RJ", "parent": "India", "aliases": ["RJ"]},
    {"name": "Sikkim", "normalized_name": "sikkim", "location_type": "STATE", "country_code": "IN", "state_code": "SK", "parent": "India", "aliases": ["SK"]},
    {
        "name": "Tamil Nadu",
        "normalized_name": "tamil nadu",
        "location_type": "STATE",
        "country_code": "IN",
        "state_code": "TN",
        "parent": "India",
        "aliases": ["TN", "Madras State", "Tamil Nadu Government", "TN Govt"],
    },
    {"name": "Telangana", "normalized_name": "telangana", "location_type": "STATE", "country_code": "IN", "state_code": "TG", "parent": "India", "aliases": ["TG"]},
    {"name": "Tripura", "normalized_name": "tripura", "location_type": "STATE", "country_code": "IN", "state_code": "TR", "parent": "India", "aliases": ["TR"]},
    {"name": "Uttar Pradesh", "normalized_name": "uttar pradesh", "location_type": "STATE", "country_code": "IN", "state_code": "UP", "parent": "India", "aliases": ["UP"]},
    {"name": "Uttarakhand", "normalized_name": "uttarakhand", "location_type": "STATE", "country_code": "IN", "state_code": "UK", "parent": "India", "aliases": ["UK", "Uttaranchal"]},
    {"name": "West Bengal", "normalized_name": "west bengal", "location_type": "STATE", "country_code": "IN", "state_code": "WB", "parent": "India", "aliases": ["WB"]},

    # Key Cities & Districts
    {
        "name": "Coimbatore",
        "normalized_name": "coimbatore",
        "location_type": "DISTRICT",
        "country_code": "IN",
        "state_code": "TN",
        "district_code": "COIMBATORE",
        "parent": "Tamil Nadu",
        "aliases": ["Kovai"],
    },
    {
        "name": "Chennai",
        "normalized_name": "chennai",
        "location_type": "CITY",
        "country_code": "IN",
        "state_code": "TN",
        "district_code": "CHENNAI",
        "parent": "Tamil Nadu",
        "aliases": ["Madras"],
    },
    {
        "name": "Mumbai",
        "normalized_name": "mumbai",
        "location_type": "CITY",
        "country_code": "IN",
        "state_code": "MH",
        "district_code": "MUMBAI",
        "parent": "Maharashtra",
        "aliases": ["Bombay"],
    },
    {
        "name": "Bengaluru",
        "normalized_name": "bengaluru",
        "location_type": "CITY",
        "country_code": "IN",
        "state_code": "KA",
        "district_code": "BANGALORE",
        "parent": "Karnataka",
        "aliases": ["Bangalore"],
    },
    {
        "name": "New Delhi",
        "normalized_name": "new delhi",
        "location_type": "CITY",
        "country_code": "IN",
        "state_code": "DL",
        "parent": "India",
        "aliases": ["Delhi", "NCR", "National Capital Region"],
    },
    # Other Global Countries
    {
        "name": "United States",
        "normalized_name": "united states",
        "location_type": "COUNTRY",
        "country_code": "US",
        "parent": "World",
        "aliases": ["USA", "US", "America"],
    },
    {
        "name": "United Kingdom",
        "normalized_name": "united kingdom",
        "location_type": "COUNTRY",
        "country_code": "GB",
        "parent": "World",
        "aliases": ["UK", "Britain", "Great Britain"],
    },
]


def seed_geographic_locations(db: Session) -> List[GeographicLocation]:
    """Seed reference geographic location hierarchy into DB if not present."""
    name_to_obj: Dict[str, GeographicLocation] = {}

    existing = db.query(GeographicLocation).all()
    for loc in existing:
        name_to_obj[loc.name] = loc

    added_any = False
    for item in REFERENCE_LOCATIONS:
        if item["name"] in name_to_obj:
            continue

        parent_obj = name_to_obj.get(item.get("parent")) if item.get("parent") else None
        loc = GeographicLocation(
            name=item["name"],
            normalized_name=item["normalized_name"],
            location_type=item["location_type"],
            country_code=item.get("country_code"),
            state_code=item.get("state_code"),
            district_code=item.get("district_code"),
            parent_id=parent_obj.id if parent_obj else None,
        )
        loc.aliases = item.get("aliases", [])
        db.add(loc)
        db.commit()
        db.refresh(loc)
        name_to_obj[loc.name] = loc
        added_any = True

    return list(name_to_obj.values())


class GeographicLocationExtractor:
    """Deterministic extractor matching text against known reference locations."""

    def __init__(self, db: Session):
        self.db = db
        self.locations = seed_geographic_locations(db)

    def extract_locations(self, text: str) -> List[Tuple[GeographicLocation, float, str]]:
        """
        Extract geographic locations mentioned in text.
        Returns list of (GeographicLocation, confidence, relation_type).
        """
        if not text:
            return []

        text_lower = text.lower()
        found: List[Tuple[GeographicLocation, float, str]] = []
        seen_ids: Set[int] = set()

        for loc in self.locations:
            if loc.id in seen_ids:
                continue

            matched = False
            confidence = 0.8
            # Check canonical name
            if loc.normalized_name in text_lower:
                matched = True
                confidence = 0.95 if loc.location_type in ("DISTRICT", "CITY") else 0.85
            else:
                # Check aliases
                for alias in loc.aliases:
                    if len(alias) > 2 and alias.lower() in text_lower:
                        matched = True
                        confidence = 0.75
                        break

            if matched:
                relation = "PRIMARY" if loc.location_type in ("DISTRICT", "CITY", "STATE") else "MENTIONED"
                found.append((loc, confidence, relation))
                seen_ids.add(loc.id)

        # Default fallback to India if no specific location found
        if not found:
            india = next((l for l in self.locations if l.normalized_name == "india"), None)
            if india:
                found.append((india, 0.5, "MENTIONED"))

        return found


class LocationService:
    """Hierarchical Location query service."""

    def __init__(self, db: Session):
        self.db = db
        self.extractor = GeographicLocationExtractor(db)

    def get_location(self, location_id: int) -> Optional[GeographicLocation]:
        return self.db.query(GeographicLocation).filter(GeographicLocation.id == location_id).first()

    def find_by_name(self, name_query: str) -> Optional[GeographicLocation]:
        norm = name_query.strip().lower()
        all_locs = seed_geographic_locations(self.db)
        for loc in all_locs:
            if loc.normalized_name == norm or loc.name.lower() == norm:
                return loc
            for alias in (loc.aliases or []):
                if alias.lower() == norm:
                    return loc
        return None

    def list_locations(self, parent_id: Optional[int] = None) -> List[Dict[str, Any]]:
        query = self.db.query(GeographicLocation).filter(GeographicLocation.active == True)
        if parent_id is not None:
            query = query.filter(GeographicLocation.parent_id == parent_id)
        locations = query.order_by(GeographicLocation.name).all()

        return [
            {
                "id": loc.id,
                "name": loc.name,
                "normalized_name": loc.normalized_name,
                "location_type": loc.location_type,
                "parent_id": loc.parent_id,
                "country_code": loc.country_code,
                "state_code": loc.state_code,
                "district_code": loc.district_code,
                "aliases": loc.aliases,
            }
            for loc in locations
        ]

    def get_location_tree(self) -> List[Dict[str, Any]]:
        """Return full hierarchical location tree."""
        all_locs = seed_geographic_locations(self.db)

        by_id = {
            loc.id: {
                "id": loc.id,
                "name": loc.name,
                "location_type": loc.location_type,
                "parent_id": loc.parent_id,
                "country_code": loc.country_code,
                "state_code": loc.state_code,
                "district_code": loc.district_code,
                "children": [],
            }
            for loc in all_locs
        }

        tree = []
        for loc_id, item in by_id.items():
            parent_id = item["parent_id"]
            if parent_id and parent_id in by_id:
                by_id[parent_id]["children"].append(item)
            else:
                tree.append(item)

        return tree

    def attach_locations_to_event(self, event: Event) -> List[EventLocation]:
        """Extract and persist location relations for an event."""
        text = f"{event.title} {event.summary or ''}"
        extracted = self.extractor.extract_locations(text)

        event_locs: List[EventLocation] = []
        for loc, conf, rel_type in extracted:
            existing = self.db.query(EventLocation).filter(
                EventLocation.event_id == event.id,
                EventLocation.location_id == loc.id,
            ).first()

            if not existing:
                el = EventLocation(
                    event_id=event.id,
                    location_id=loc.id,
                    relation_type=rel_type,
                    confidence=conf,
                )
                self.db.add(el)
                event_locs.append(el)
            else:
                event_locs.append(existing)

        if event_locs:
            try:
                self.db.commit()
            except Exception:
                self.db.rollback()

        return event_locs

    def _get_all_descendant_ids(self, location_id: int) -> Set[int]:
        descendants = {location_id}
        to_process = [location_id]

        while to_process:
            current_parent = to_process.pop()
            children = (
                self.db.query(GeographicLocation.id)
                .filter(
                    GeographicLocation.parent_id == current_parent,
                    GeographicLocation.active == True,
                )
                .all()
            )
            for (child_id,) in children:
                if child_id not in descendants:
                    descendants.add(child_id)
                    to_process.append(child_id)

        return descendants

    def get_location_events(
        self, location_id: int, limit: int = 20, offset: int = 0
    ) -> Dict[str, Any]:
        """Return events associated with location_id or its descendants."""
        loc = self.get_location(location_id)
        if not loc:
            return {"location": None, "total": 0, "events": []}

        child_ids = list(self._get_all_descendant_ids(location_id))

        q = self.db.query(Event).join(EventLocation).filter(EventLocation.location_id.in_(child_ids))
        total = q.count()
        events = q.order_by(Event.event_date.desc()).offset(offset).limit(limit).all()

        return {
            "location": {
                "id": loc.id,
                "name": loc.name,
                "location_type": loc.location_type,
                "country_code": loc.country_code,
                "state_code": loc.state_code,
            },
            "total": total,
            "limit": limit,
            "offset": offset,
            "events": [
                {
                    "id": e.id,
                    "title": e.title,
                    "summary": e.summary,
                    "domain": e.domain,
                    "event_type": e.event_type,
                    "event_date": e.event_date.isoformat(),
                    "importance_score": e.importance_score,
                }
                for e in events
            ],
        }

    def get_source_coverage(self) -> Dict[str, Any]:
        """Return measurable geographic coverage statistics across ingestion sources."""
        total_sources = self.db.query(Source).count()
        enabled_sources = self.db.query(Source).filter(Source.enabled == True).count()
        total_locations = self.db.query(GeographicLocation).count()
        mapped_events = self.db.query(EventLocation.event_id).distinct().count()

        counts_by_type = (
            self.db.query(
                GeographicLocation.location_type,
                func.count(GeographicLocation.id),
            )
            .group_by(GeographicLocation.location_type)
            .all()
        )

        type_map = {loc_type: count for loc_type, count in counts_by_type}

        return {
            "total_sources": total_sources,
            "enabled_sources": enabled_sources,
            "total_reference_locations": total_locations,
            "events_with_geographic_mapping": mapped_events,
            "coverage_breakdown": [
                {"level": "WORLD", "count": type_map.get("WORLD", 0)},
                {"level": "COUNTRY", "count": type_map.get("COUNTRY", 0)},
                {"level": "STATE", "count": type_map.get("STATE", 0)},
                {"level": "DISTRICT/CITY", "count": type_map.get("DISTRICT", 0) + type_map.get("CITY", 0)},
            ],
        }
