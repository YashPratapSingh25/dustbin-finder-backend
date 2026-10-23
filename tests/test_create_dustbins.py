
from datetime import datetime, timezone
from io import BytesIO
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from PIL import Image
from main import app
from router.dustbin_router import get_dustbin_service
from service.dustbin_service import DustbinService
from schemas.dustbin_schemas import DustbinResponse
from core.dependencies import get_db_session
from core.exceptions import ConflictException
from schemas.dustbin_schemas import NearbyDustbinConflict
import core.dependencies as image_module


@pytest.fixture
def valid_form():
    return {
        "name": "Public Dustbin",
        "latitude": "22.7196",
        "longitude": "75.8577",
        "address": "MG Road, Indore",
    }


@pytest.fixture
def valid_image():
    buffer = BytesIO()
    Image.new("RGB", (10, 10), color="green").save(
        buffer, format="PNG"
    )
    return buffer.getvalue()


@pytest.fixture
def dustbin_response():
    now = datetime.now(timezone.utc)

    return DustbinResponse.model_construct(
        id=uuid4(),
        name="Public Dustbin",
        latitude=22.7196,
        longitude=75.8577,
        address="MG Road, Indore",
        photos_keys=["dustbin_images/test.jpeg"],
        photo_urls=["https://example.com/image"],
        confidence_score=0,
        report_count=0,
        last_verified_at=None,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def mock_dustbin_service():
    service = AsyncMock(spec=DustbinService)
    original_overrides = app.dependency_overrides.copy()

    async def override_service():
        return service

    app.dependency_overrides[get_dustbin_service] = override_service

    yield service

    app.dependency_overrides.clear()
    app.dependency_overrides.update(original_overrides)


def image_files(*images):
    return [
        ("images", (f"image_{i}.png", image, "image/png"))
        for i, image in enumerate(images)
    ]


# 1. Successful creation with one valid image
@pytest.mark.asyncio
async def test_create_dustbin_success(
    client, valid_form, valid_image,
    mock_dustbin_service, dustbin_response
):
    mock_dustbin_service.create_dustbin.return_value = dustbin_response

    response = await client.post(
        "/dustbin/",
        data=valid_form,
        files=image_files(valid_image),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Dustbin added successfully"
    assert body["result"]["name"] == "Public Dustbin"
    assert len(body["result"]["photo_urls"]) == 1


# 2. Successful creation with five valid images
@pytest.mark.asyncio
async def test_create_dustbin_accepts_five_images(
    client, valid_form, valid_image,
    mock_dustbin_service, dustbin_response
):
    mock_dustbin_service.create_dustbin.return_value = dustbin_response

    response = await client.post(
        "/dustbin/",
        data=valid_form,
        files=image_files(*([valid_image] * 5)),
    )

    assert response.status_code == 200
    assert len(
        mock_dustbin_service.create_dustbin.await_args.kwargs[
            "images_bytes"
        ]
    ) == 5


# 3. Reject a request with no images
@pytest.mark.asyncio
async def test_create_dustbin_rejects_no_images(
    client, valid_form, mock_dustbin_service
):
    response = await client.post("/dustbin/", data=valid_form)

    assert response.status_code == 422
    mock_dustbin_service.create_dustbin.assert_not_awaited()


# 4. Reject more than five images
@pytest.mark.asyncio
async def test_create_dustbin_rejects_six_images(
    client, valid_form, valid_image, mock_dustbin_service
):
    response = await client.post(
        "/dustbin/",
        data=valid_form,
        files=image_files(*([valid_image] * 6)),
    )

    assert response.status_code == 400
    mock_dustbin_service.create_dustbin.assert_not_awaited()


# 5. Reject a missing required form field
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "field",
    ["name", "latitude", "longitude", "address"],
)
async def test_create_dustbin_missing_field(
    client, valid_form, valid_image, field,
    mock_dustbin_service
):
    data = valid_form.copy()
    data.pop(field)

    response = await client.post(
        "/dustbin/",
        data=data,
        files=image_files(valid_image),
    )

    assert response.status_code == 422
    mock_dustbin_service.create_dustbin.assert_not_awaited()


# 6. Reject non-numeric coordinates
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("latitude", "north"),
        ("longitude", "east"),
    ],
)
async def test_create_dustbin_invalid_coordinates(
    client, valid_form, valid_image, field, value,
    mock_dustbin_service
):
    data = valid_form.copy()
    data[field] = value

    response = await client.post(
        "/dustbin/",
        data=data,
        files=image_files(valid_image),
    )

    assert response.status_code == 422
    mock_dustbin_service.create_dustbin.assert_not_awaited()


# 7. Accept coordinates at zero
@pytest.mark.asyncio
async def test_create_dustbin_zero_coordinates(
    client, valid_form, valid_image,
    mock_dustbin_service, dustbin_response
):
    mock_dustbin_service.create_dustbin.return_value = dustbin_response
    data = valid_form | {"latitude": "0", "longitude": "0"}

    response = await client.post(
        "/dustbin/",
        data=data,
        files=image_files(valid_image),
    )

    assert response.status_code == 200
    schema = mock_dustbin_service.create_dustbin.await_args.args[0]
    assert schema.latitude == 0.0
    assert schema.longitude == 0.0


# 8. Reject corrupt image bytes
@pytest.mark.asyncio
async def test_create_dustbin_corrupt_image(
    client, valid_form, mock_dustbin_service
):
    response = await client.post(
        "/dustbin/",
        data=valid_form,
        files=image_files(b"this is not an image"),
    )

    assert response.status_code == 415
    mock_dustbin_service.create_dustbin.assert_not_awaited()


# 9. Reject a valid but unsupported image format (BMP)
@pytest.mark.asyncio
async def test_create_dustbin_unsupported_image_format(
    client, valid_form, mock_dustbin_service
):
    buffer = BytesIO()
    Image.new("RGB", (10, 10)).save(buffer, format="BMP")

    response = await client.post(
        "/dustbin/",
        data=valid_form,
        files=[
            ("images", ("image.bmp", buffer.getvalue(), "image/bmp"))
        ],
    )

    assert response.status_code == 415
    mock_dustbin_service.create_dustbin.assert_not_awaited()


# 10. Reject an image that exceeds the configured size limit
@pytest.mark.asyncio
async def test_create_dustbin_image_too_large(
    client, valid_form, valid_image,
    mock_dustbin_service, monkeypatch
):
    monkeypatch.setattr(image_module, "MAX_SIZE", 10)

    response = await client.post(
        "/dustbin/",
        data=valid_form,
        files=image_files(valid_image),
    )

    assert response.status_code == 413
    mock_dustbin_service.create_dustbin.assert_not_awaited()


# 11. Reject a missing image form field
@pytest.mark.asyncio
async def test_create_dustbin_missing_image_field(
    client, valid_form, mock_dustbin_service
):
    response = await client.post("/dustbin/", data=valid_form)

    assert response.status_code == 422
    mock_dustbin_service.create_dustbin.assert_not_awaited()


# 12. Ensure validated image bytes reach the service unchanged
@pytest.mark.asyncio
async def test_create_dustbin_passes_image_bytes_to_service(
    client, valid_form, valid_image,
    mock_dustbin_service, dustbin_response
):
    mock_dustbin_service.create_dustbin.return_value = dustbin_response

    response = await client.post(
        "/dustbin/",
        data=valid_form,
        files=image_files(valid_image),
    )

    assert response.status_code == 200
    kwargs = mock_dustbin_service.create_dustbin.await_args.kwargs
    assert kwargs["images_bytes"] == [valid_image]


# 13. Ensure the service receives the expected request schema
@pytest.mark.asyncio
async def test_create_dustbin_passes_correct_schema(
    client, valid_form, valid_image,
    mock_dustbin_service, dustbin_response
):
    mock_dustbin_service.create_dustbin.return_value = dustbin_response

    await client.post(
        "/dustbin/",
        data=valid_form,
        files=image_files(valid_image),
    )

    schema = mock_dustbin_service.create_dustbin.await_args.args[0]
    assert schema.name == "Public Dustbin"
    assert schema.latitude == 22.7196
    assert schema.longitude == 75.8577
    assert schema.address == "MG Road, Indore"


# 14. Verify an application conflict is returned to the client
@pytest.mark.asyncio
async def test_create_dustbin_duplicate_conflict(
    client, valid_form, valid_image, mock_dustbin_service
):
    existing = NearbyDustbinConflict(
        id=uuid4(),
        latitude=22.7196,
        longitude=75.8577,
        address="MG Road, Indore",
        name="Existing Dustbin",
        distance_in_m=10.0,
        photo_urls=["https://example.com/existing"],
    )

    mock_dustbin_service.create_dustbin.side_effect = ConflictException(
        result=existing,
        message="Dustbin already exists",
    )

    response = await client.post(
        "/dustbin/",
        data=valid_form,
        files=image_files(valid_image),
    )

    assert response.status_code == 409
