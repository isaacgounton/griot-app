import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

sys.modules.setdefault("srt", SimpleNamespace(parse=lambda *_args, **_kwargs: []))

from app.services.video_pipeline.models import AudioResult, PipelineParams
from app.services.video_pipeline.steps.caption_step import render_captions


async def test_render_captions_uses_clean_tts_word_timestamps():
    params = PipelineParams(
        add_captions=True,
        caption_style="viral_bounce",
        width=1080,
        height=1920,
        caption_properties={},
        language="en",
    )
    audio_result = AudioResult(
        audio_url="https://example.com/audio.mp3",
        audio_duration=2.0,
        word_timestamps=[
            {"word": "Hello", "start": 0.0, "end": 0.5},
            {"word": "world", "start": 0.5, "end": 1.0},
        ],
    )

    with patch(
        "app.services.video_pipeline.steps.caption_step.advanced_caption_service.process_caption_job",
        new=AsyncMock(return_value={"url": "https://example.com/captioned.mp4", "srt_url": "https://example.com/captioned.srt"}),
    ) as mock_process:
        result = await render_captions(
            "https://example.com/video.mp4",
            "Hello world",
            params,
            audio_result,
        )

    assert result.video_url == "https://example.com/captioned.mp4"
    assert result.srt_url == "https://example.com/captioned.srt"

    sent_params = mock_process.await_args.args[1]
    assert sent_params["captions"] == "Hello world"
    assert sent_params["transcription_result"]["language"] == "en"
    assert sent_params["transcription_result"]["segments"][0]["words"] == audio_result.word_timestamps


async def test_render_captions_falls_back_without_clean_tts_word_timestamps():
    params = PipelineParams(
        add_captions=True,
        caption_style="viral_bounce",
        width=1080,
        height=1920,
        caption_properties={},
        language="en",
    )

    with patch(
        "app.services.video_pipeline.steps.caption_step.advanced_caption_service.process_caption_job",
        new=AsyncMock(return_value={"url": "https://example.com/captioned.mp4", "srt_url": None}),
    ) as mock_process:
        await render_captions(
            "https://example.com/video.mp4",
            "Hello world",
            params,
            AudioResult(audio_url="https://example.com/audio.mp3", audio_duration=2.0, word_timestamps=[]),
        )

    sent_params = mock_process.await_args.args[1]
    assert sent_params["transcription_result"] is None
