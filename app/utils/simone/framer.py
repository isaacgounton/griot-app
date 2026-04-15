from __future__ import annotations

import cv2
import logging

logger = logging.getLogger(__name__)


class Framer:
    def __init__(self, filename, num_frames=10):
        self.filename = filename
        self.num_frames = num_frames

    def get_video_frames(self):
        frames = []
        cap = cv2.VideoCapture(self.filename)

        if not cap.isOpened():
            logger.warning(f"Could not open video: {self.filename}")
            return frames

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            cap.release()
            return frames

        # Calculate which frames to extract
        num_to_extract = min(self.num_frames, total_frames)
        interval = total_frames / num_to_extract

        for i in range(num_to_extract):
            target_frame = int(i * interval)
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            ret, frame = cap.read()
            if ret:
                frames.append(frame)

        cap.release()
        return frames
