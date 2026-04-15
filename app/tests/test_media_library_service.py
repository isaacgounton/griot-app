import pytest

from app.services.dashboard.media_library_service import MediaLibraryService
from app.database import MediaType


@pytest.mark.asyncio
async def test_extract_primary_url_document_image_url():
    svc = MediaLibraryService()
    result = {"image_url": "https://example.com/myimage.jpg"}
    primary = svc._extract_primary_url(result, MediaType.DOCUMENT)
    assert primary == "https://example.com/myimage.jpg"


@pytest.mark.asyncio
async def test_extract_primary_url_document_file_url():
    svc = MediaLibraryService()
    result = {"file_url": "https://s3.amazonaws.com/bucket/document.pdf"}
    primary = svc._extract_primary_url(result, MediaType.DOCUMENT)
    assert primary == "https://s3.amazonaws.com/bucket/document.pdf"


@pytest.mark.asyncio
async def test_extract_primary_url_document_none():
    svc = MediaLibraryService()
    result = {"text": "This is a test."}
    primary = svc._extract_primary_url(result, MediaType.DOCUMENT)
    assert primary is None
