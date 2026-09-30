from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.location_service import LocationService
from app.core.cache import cache_get, cache_set

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("")
def get_locations(
    parent_id: Optional[int] = Query(None, description="Filter by parent location ID"),
    db: Session = Depends(get_db),
):
    """Return list of locations or tree nodes."""
    cache_key = f"flashfacts:locations:list:{parent_id or 'all'}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    service = LocationService(db)
    result = service.list_locations(parent_id=parent_id)
    cache_set(cache_key, result, ttl=600)
    return result


@router.get("/tree")
def get_location_tree(db: Session = Depends(get_db)):
    """Return complete hierarchical location tree."""
    cache_key = "flashfacts:locations:tree"
    cached = cache_get(cache_key)
    if cached:
        return cached

    result = LocationService(db).get_location_tree()
    cache_set(cache_key, result, ttl=600)
    return result


@router.get("/{location_id}")
def get_location(location_id: int, db: Session = Depends(get_db)):
    """Return location details."""
    service = LocationService(db)
    loc = service.get_location(location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    return {
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


@router.get("/{location_id}/events")
def get_location_events(
    location_id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Return current affairs events associated with a location."""
    service = LocationService(db)
    res = service.get_location_events(location_id, limit=limit, offset=offset)
    if not res.get("location"):
        raise HTTPException(status_code=404, detail="Location not found")
    return res
