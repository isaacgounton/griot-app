import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

sys.modules.setdefault(
    "any_llm",
    SimpleNamespace(
        AnyLLM=object,
        LLMProvider=object,
        acompletion=None,
        aresponses=None,
        alist_models=None,
    ),
)
sys.modules.setdefault(
    "app.services.ai.unified_ai_service",
    SimpleNamespace(unified_ai_service=SimpleNamespace()),
)

from app.services.pollinations.pollinations_service import PollinationsService


async def test_generate_audio_tts_uses_dedicated_audio_endpoint():
    service = PollinationsService()

    with patch.object(service, "_make_request", new=AsyncMock(return_value=b"audio-bytes")) as mock_request, \
         patch.object(service, "save_generated_content_to_s3", new=AsyncMock(return_value="https://example.com/audio.mp3")):
        result = await service.generate_audio_tts(
            text="Hello world",
            voice="nova",
            model="openai-audio",
            response_format="mp3",
            speed=1.2,
            return_url=True,
        )

    assert result == "https://example.com/audio.mp3"
    assert mock_request.await_args.args[0] == "GET"
    endpoint = mock_request.await_args.args[1]
    assert endpoint.startswith("/audio/Hello%20world?")
    assert "voice=nova" in endpoint
    assert "model=openai-audio" in endpoint
    assert "response_format=mp3" in endpoint
    assert "speed=1.2" in endpoint


async def test_generate_video_uses_dedicated_video_endpoint():
    service = PollinationsService()

    with patch("aiohttp.ClientSession") as mock_session_cls:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=b"video-bytes")

        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_response
        mock_context.__aexit__.return_value = None

        mock_session = MagicMock()
        mock_session.get.return_value = mock_context

        mock_session_context = AsyncMock()
        mock_session_context.__aenter__.return_value = mock_session
        mock_session_context.__aexit__.return_value = None
        mock_session_cls.return_value = mock_session_context

        result = await service.generate_video(
            prompt="Sunset timelapse",
            model="veo",
            duration=4,
            aspect_ratio="16:9",
            audio=True,
            width=1024,
            height=576,
            image_url="https://example.com/frame.png",
        )

    assert result == b"video-bytes"
    called_url = mock_session.get.call_args.args[0]
    assert called_url.startswith("https://gen.pollinations.ai/video/Sunset%20timelapse?")
    assert "model=veo" in called_url
    assert "duration=4" in called_url
    assert "aspectRatio=16%3A9" in called_url
    assert "audio=true" in called_url
    assert "width=1024" in called_url
    assert "height=576" in called_url
    assert "image=https%3A%2F%2Fexample.com%2Fframe.png" in called_url
