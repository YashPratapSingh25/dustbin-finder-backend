from datetime import datetime, timezone
from uuid import uuid4, uuid7

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from model.dustbin import Dustbin
from unittest.mock import AsyncMock, MagicMock, patch

from schemas.base_schema import Pagination
from service.dustbin_service import DustbinService

def make_dustbin(
    *,
    name: str,
    latitude: float,
    longitude: float,
) -> Dustbin:
    return Dustbin(
        name=name,
        latitude=latitude,
        longitude=longitude,
        address=f"Test address for {name}",
        photos_keys=[],
        confidence_score=50.0,
        report_count=1,
    )

# API call without lat lng
@pytest.mark.asyncio
async def test_nearby_dustbins_coordinates_requirements(client):
    response = await client.get("/dustbin/nearby")
    assert response.status_code == 422

# Success Response
@pytest.mark.asyncio
async def test_nearby_dustbins_returns_success(client, db_session : AsyncSession):
    nearby_one = make_dustbin(
        name="new green pg",
        latitude=23.04904853564418, 
        longitude=72.50738689747713
    )

    nearby_two = make_dustbin(
        name="random dustbin",
        latitude=23.04813385706992, 
        longitude=72.50702215478496
    )

    office = make_dustbin(
        name="office",
        latitude=23.032741638802694, 
        longitude=72.50776726972843,
    )

    metro = make_dustbin(
        name="Metro",
        latitude=23.050334424559065, 
        longitude=72.50800803293937
    )

    hotel = make_dustbin(
        name="hotel",
        latitude=23.047900988375467, 
        longitude=72.50848302886756
    )

    chai = make_dustbin(
        name="chai",
        latitude=23.048763250762878, 
        longitude=72.50892723252016
    )

    pav = make_dustbin(
        name="pav",
        latitude=23.049000187532712, 
        longitude=72.50888632883255
    )

    db_session.add_all([nearby_one, nearby_two, office, metro, hotel, chai, pav])

    await db_session.flush()
    await db_session.commit()


    response = await client.get(
        "/dustbin/nearby",
        params={
            "latitude": 23.049042945671633,
            "longitude": 72.50743191455975,
            "radius_in_m": 500,
            "page_number": 1,
            "page_size": 5,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Nearby dustbins fetched successfully"
    assert "result" in body
    assert "metadata" in body
    assert body["metadata"]["page_number"] == 1
    assert body["metadata"]["page_size"] == 5
    assert body["metadata"]["total_items"] == 6
    assert len(body["result"]) == 5


# When no nearby dustbins exists within lat lng (also success)
@pytest.mark.asyncio
async def test_empty_success_response(client):
    response = await client.get(
        "/dustbin/nearby",
        params={
            "latitude": 40.68933885866274,
            "longitude": -74.04451113154299,
            "radius_in_m": 500,
            "page_number": 1,
            "page_size": 5,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["result"] == []

    # Routing Service Failure Fallback Test
@pytest.mark.asyncio
async def test_nearby_dustbins_routing_service_failure_fallback(client, db_session: AsyncSession):
    dustbin = make_dustbin(
        name="fallback test dustbin",
        latitude=23.049048,
        longitude=72.507386
    )
    db_session.add(dustbin)
    await db_session.commit()

    with patch("service.dustbin_service.RoutingService.get_distance_duration", side_effect=Exception("Routing API Down")):
        response = await client.get(
            "/dustbin/nearby",
            params={
                "latitude": 23.0490,
                "longitude": 72.5074,
                "radius_in_m": 500,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Nearby dustbins fetched successfully"
    assert len(body["result"]) == 1
    # Ensure distance fallback was calculated and populated
    assert "distance_in_m" in body["result"][0]


# Routing Service Success & Sorting Test
@pytest.mark.asyncio
async def test_nearby_dustbins_routing_sorting_and_rounding(client, db_session: AsyncSession):
    d1 = make_dustbin(name="Near", latitude=23.049, longitude=72.507)
    d2 = make_dustbin(name="Far", latitude=23.050, longitude=72.508)
    db_session.add_all([d1, d2])
    await db_session.commit()

    # Mock routing result to return specific distances (e.g., d2 is closer than d1 after routing)
    mock_routing_response = ([12.0, 15.0], [255.0, 123.0])  # (durations, distances in meters)

    with patch("service.dustbin_service.RoutingService.get_distance_duration", new_callable=AsyncMock) as mock_routing:
        mock_routing.return_value = mock_routing_response

        response = await client.get(
            "/dustbin/nearby",
            params={
                "latitude": 23.049,
                "longitude": 72.507,
                "radius_in_m": 500,
            },
        )

    assert response.status_code == 200
    body = response.json()
    results = body["result"]
    
    # Check rounding to multiple of 10 and sorting (123.0 rounds to 120, 255.0 rounds to 260)
    distances = [item["distance_in_m"] for item in results]
    assert distances == sorted(distances)
    assert 120 in distances
    assert 260 in distances


# Out-of-Bounds Pagination Test
@pytest.mark.asyncio
async def test_nearby_dustbins_pagination_out_of_bounds(client, db_session: AsyncSession):
    dustbin = make_dustbin(name="Single Dustbin", latitude=23.049, longitude=72.507)
    db_session.add(dustbin)
    await db_session.commit()

    response = await client.get(
        "/dustbin/nearby",
        params={
            "latitude": 23.049,
            "longitude": 72.507,
            "radius_in_m": 500,
            "page_number": 99,
            "page_size": 10,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["result"] == []
    assert body["metadata"]["page_number"] == 99
    assert body["metadata"]["has_next"] is False
    assert body["metadata"]["has_previous"] is True
    assert body["metadata"]["total_pages"] == 1

@pytest.mark.asyncio
async def test_dustbin_service_get_nearby_dustbins_unit():
    # Arrange mocks
    mock_repo = AsyncMock()
    mock_routing_service = AsyncMock()
    mock_s3_service = AsyncMock()
    
    mock_dustbin = MagicMock(
        id=uuid7(),
        latitude=23.0,
        longitude=72.0,
        address="Mock Address",
        photos_keys=["key1", "key2"],
        photo_urls=["url1", "url2"],
        confidence_score=90.0,
        report_count=2,
        last_verified_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    mock_dustbin.name = "Mock Bin"
    mock_repo.get_nearby_centers_count.return_value = 1
    mock_repo.get_nearby_dustbins.return_value = [(mock_dustbin, 0.25)]  # 0.25 km = 250m

    # Mock routing service response
    mock_routing_service.get_distance_duration.return_value = ([30.0], [245.0]) # 245m -> rounds to 250

    service = DustbinService(dustbin_repo=mock_repo, routing_service=mock_routing_service, s3_service=mock_s3_service)
    
    # Mock photo URL helper method on service instance
    service._get_photos_url = AsyncMock(return_value=["http://example.com/photo.jpg"])

    pagination = Pagination(page_number=1, page_size=10, limit=10, offset=0)

    # Act
    result = await service.get_nearby_dustbins(
        latitude=23.0,
        longitude=72.0,
        radius_in_m=500,
        pagination=pagination
    )

    # Assert
    assert result.total_items == 1
    assert len(result.result) == 1
    
    item = result.result[0]
    assert item.name == "Mock Bin"
    assert item.distance_in_m == 250  # 245 rounded to nearest 10
    assert item.photo_urls == ["http://example.com/photo.jpg"]
    
    mock_repo.get_nearby_centers_count.assert_awaited_once()
    mock_repo.get_nearby_dustbins.assert_awaited_once()
    mock_routing_service.get_distance_duration.assert_awaited_once()