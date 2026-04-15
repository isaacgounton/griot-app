"""Document skill — convert documents to markdown using Marker."""

import asyncio
import os
import tempfile
import uuid
from typing import Any

import aiohttp

from app.services.tools.skills.base import Skill

skill = Skill(name="document", description="Convert documents to readable markdown")


async def _poll_job(job_id: str, timeout: int = 300) -> dict[str, Any]:
    from app.services.job_queue import job_queue

    elapsed = 0
    interval = 3
    while elapsed < timeout:
        job_info = await job_queue.get_job(job_id)
        if job_info is None:
            return {"error": f"Job {job_id} not found"}

        status = getattr(job_info, "status", None)
        if status is not None:
            status_val = status.value if hasattr(status, "value") else str(status)
        else:
            status_val = "unknown"

        if status_val == "completed":
            return {"result": getattr(job_info, "result", None) or {}}
        elif status_val == "failed":
            return {"error": str(getattr(job_info, "error", "Job failed"))}

        await asyncio.sleep(interval)
        elapsed += interval

    return {"error": f"Job timed out after {timeout}s", "job_id": job_id}


async def _convert_to_markdown(args: dict[str, Any]) -> dict[str, Any]:
    from app.services.documents.marker_service import marker_service
    from app.services.job_queue import job_queue
    from app.models import JobType

    file_url = args.get("file_url")
    if not file_url:
        return {"error": "file_url is required"}

    # Download the file to a temp path for Marker
    file_path = None
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as response:
                if response.status != 200:
                    return {"error": f"Failed to download file: HTTP {response.status}"}

                # Determine extension from URL or content-type
                content_type = response.headers.get("content-type", "")
                ext = ".pdf"
                url_ext = os.path.splitext(file_url.split("?")[0])[1].lower()
                if url_ext in (".pdf", ".docx", ".doc", ".pptx", ".xlsx", ".png", ".jpg", ".jpeg", ".html", ".epub"):
                    ext = url_ext
                elif "word" in content_type:
                    ext = ".docx"
                elif "image" in content_type:
                    ext = ".png"

                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                    tmp.write(await response.read())
                    file_path = tmp.name
    except Exception as e:
        return {"error": f"Failed to download file: {e}"}

    job_data = {
        "file_path": file_path,
        "output_format": args.get("output_format", "markdown"),
        "force_ocr": args.get("force_ocr", False),
        "preserve_images": args.get("preserve_images", True),
        "use_llm": False,
        "paginate_output": False,
        "original_filename": args.get("filename", os.path.basename(file_url.split("?")[0])),
    }

    job_id = str(uuid.uuid4())

    async def marker_wrapper(_job_id: str, data: dict[str, Any]) -> dict[str, Any]:
        return await marker_service.convert_document(data)

    await job_queue.add_job(
        job_id=job_id,
        job_type=JobType.MARKER_DOCUMENT_CONVERSION,
        process_func=marker_wrapper,
        data=job_data,
    )

    result = await _poll_job(job_id, timeout=300)
    if result.get("error"):
        return {**result, "job_id": job_id}

    res = result.get("result", {})
    return {
        "markdown": res.get("markdown", res.get("content", "")),
        "metadata": res.get("metadata"),
        "job_id": job_id,
    }


skill.action(
    name="convert_to_markdown",
    description=(
        "Convert a document to markdown text using Marker. Supports PDF, Word, Excel, "
        "PowerPoint, HTML, EPUB, and images (OCR). Provide the document URL."
    ),
    handler=_convert_to_markdown,
    properties={
        "file_url": {
            "type": "string",
            "description": "URL of the document to convert",
        },
        "filename": {
            "type": "string",
            "description": "Original filename (helps with format detection)",
        },
        "output_format": {
            "type": "string",
            "enum": ["markdown", "json", "html"],
            "description": "Output format",
            "default": "markdown",
        },
        "force_ocr": {
            "type": "boolean",
            "description": "Force OCR even for text-based documents",
            "default": False,
        },
    },
    required=["file_url"],
)
