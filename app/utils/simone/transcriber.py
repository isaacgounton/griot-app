from __future__ import annotations

import os

from app.services.speaches.speaches_client import speaches_client


class Transcriber:
    def __init__(self, filename, work_dir=None):
        self.filename = filename
        self.work_dir = work_dir or os.path.dirname(filename) or os.getcwd()

    async def transcribe(self):
        # Call the async Speaches client
        raw = await speaches_client.transcribe(
            file_path=self.filename,
            model="Systran/faster-whisper-base",
            response_format="verbose_json",
        )

        # Convert Speaches response to the result format the rest of the code expects
        result = {
            "text": "",
            "segments": []
        }

        for seg in raw.get("segments", []):
            result["text"] += seg.get("text", "") + " "
            result["segments"].append({
                "start": seg.get("start", 0.0),
                "end": seg.get("end", 0.0),
                "text": seg.get("text", ""),
            })

        result["text"] = result["text"].strip()

        transcription_path = os.path.join(self.work_dir, "transcription.txt")
        with open(transcription_path, "w", encoding="utf-8") as txt:
            txt.write(result["text"])

        # Use custom SRT writer with explicit UTF-8 encoding
        self._write_srt_with_utf8(result)

    def _write_srt_with_utf8(self, result):
        """Write SRT file with explicit UTF-8 encoding to prevent character corruption."""
        base_name = os.path.splitext(os.path.basename(self.filename))[0]
        srt_filename = os.path.join(self.work_dir, f"{base_name}.srt")

        with open(srt_filename, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(result["segments"], start=1):
                start_time = self._format_timestamp(segment["start"])
                end_time = self._format_timestamp(segment["end"])
                text = segment["text"].strip()

                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{text}\n\n")

    def _format_timestamp(self, seconds):
        """Format seconds as SRT timestamp: HH:MM:SS,mmm"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        milliseconds = int((secs - int(secs)) * 1000)

        return f"{hours:02d}:{minutes:02d}:{int(secs):02d},{milliseconds:03d}"
