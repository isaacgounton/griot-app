import asyncio
import base64
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

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
    "any_llm.exceptions",
    SimpleNamespace(MissingApiKeyError=Exception),
)
sys.modules.setdefault(
    "app.services.ai.unified_ai_service",
    SimpleNamespace(unified_ai_service=SimpleNamespace()),
)

from app.models import PollinationsVideoAnalysisRequest
from app.routes.pollinations.video import analyze_video, analyze_video_upload


class FakeUploadFile:
    def __init__(self, data: bytes, filename: str, content_type: str):
        self._data = data
        self.filename = filename
        self.content_type = content_type

    async def read(self) -> bytes:
        return self._data


class TestPollinationsVideoAnalysis:
    def test_video_analysis_url_enqueues_job(self):
        with patch(
            "app.routes.pollinations.video.job_queue.add_job",
            new_callable=AsyncMock,
        ) as mock_add_job:
            resp = asyncio.run(
                analyze_video(
                    PollinationsVideoAnalysisRequest(
                        video_url="https://example.com/sample.mp4",
                        question="Summarize the key actions",
                        model="openai-large",
                    ),
                    _={"id": "test-user"},
                )
            )

        assert resp.job_id
        assert mock_add_job.await_count == 1

        queued = mock_add_job.await_args.kwargs
        assert queued["job_type"].value == "pollinations_video_analysis"
        assert queued["data"]["video_url"] == "https://example.com/sample.mp4"
        assert queued["data"]["question"] == "Summarize the key actions"

    @patch(
        "app.routes.pollinations.video.pollinations_service.generate_text_chat",
        new_callable=AsyncMock,
        return_value="A person walks through a park.",
    )
    def test_video_analysis_url_process_uses_video_url_content(self, mock_generate_text_chat):
        with patch(
            "app.routes.pollinations.video.job_queue.add_job",
            new_callable=AsyncMock,
        ) as mock_add_job:
            resp = asyncio.run(
                analyze_video(
                    PollinationsVideoAnalysisRequest(
                        video_url="https://example.com/sample.mp4",
                        question="What happens in this clip?",
                        model="openai",
                    ),
                    _={"id": "test-user"},
                )
            )

        assert resp.job_id
        process_func = mock_add_job.await_args.kwargs["process_func"]
        queued_data = mock_add_job.await_args.kwargs["data"]

        result = asyncio.run(process_func("job-1", queued_data))

        assert result["text"] == "A person walks through a park."
        call = mock_generate_text_chat.await_args.kwargs
        assert call["model"] == "openai"
        content = call["messages"][0]["content"]
        assert content[0] == {"type": "text", "text": "What happens in this clip?"}
        assert content[1] == {
            "type": "video_url",
            "video_url": {"url": "https://example.com/sample.mp4"},
        }

    @patch(
        "app.routes.pollinations.video.pollinations_service.generate_text_chat",
        new_callable=AsyncMock,
        return_value="The video shows a quick demo.",
    )
    @patch(
        "app.routes.pollinations.video.pollinations_service.save_generated_content_to_s3",
        new_callable=AsyncMock,
        return_value="https://cdn.example.com/uploaded.mp4",
    )
    def test_video_analysis_upload_process_uses_input_video(
        self,
        mock_save_to_s3,
        mock_generate_text_chat,
    ):
        with patch(
            "app.routes.pollinations.video.job_queue.add_job",
            new_callable=AsyncMock,
        ) as mock_add_job:
            upload = FakeUploadFile(
                data=b"fake-video-bytes",
                filename="demo.mp4",
                content_type="video/mp4",
            )
            resp = asyncio.run(
                analyze_video_upload(
                    file=upload,
                    question="Describe the demo",
                    model="openai",
                    _={"id": "test-user"},
                )
            )

        assert resp.job_id

        process_func = mock_add_job.await_args.kwargs["process_func"]
        queued_data = mock_add_job.await_args.kwargs["data"]

        result = asyncio.run(process_func("job-2", queued_data))

        assert result["text"] == "The video shows a quick demo."
        assert result["video_url"] == "https://cdn.example.com/uploaded.mp4"
        mock_save_to_s3.assert_awaited_once()

        call = mock_generate_text_chat.await_args.kwargs
        content = call["messages"][0]["content"]
        assert content[0] == {"type": "text", "text": "Describe the demo"}
        assert content[1]["type"] == "input_video"
        assert content[1]["input_video"]["format"] == "mp4"
        assert base64.b64decode(content[1]["input_video"]["data"]) == b"fake-video-bytes"

    def test_video_analysis_upload_rejects_non_video(self):
        upload = FakeUploadFile(
            data=b"not-video",
            filename="demo.txt",
            content_type="text/plain",
        )

        try:
            asyncio.run(
                analyze_video_upload(
                    file=upload,
                    _={"id": "test-user"},
                )
            )
            assert False, "Expected HTTPException"
        except HTTPException as exc:
            assert exc.status_code == 400
            assert exc.detail == "File must be a video"
