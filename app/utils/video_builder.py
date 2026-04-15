from app.utils.media import media_utils
import time
from loguru import logger


class VideoBuilder:
    """
    Builder class for constructing FFmpeg video commands with a fluent interface.
    """

    def __init__(self, dimensions: tuple[int, int], ffmpeg_path="ffmpeg"):
        if not isinstance(dimensions, tuple) or len(dimensions) != 2:
            raise ValueError("Dimensions must be a tuple of (width, height).")

        self.width, self.height = dimensions
        self.ffmpeg_path = ffmpeg_path

        # Components
        self.background = None
        self.audio_file = None
        self.captions = None
        self.output_path = "output.mp4"

        # Internal state
        self.media_utils = media_utils

    def set_background_image(self, file_path: str, effect_config: dict = None):
        """Set background as an image with optional visual effects.

        Args:
            file_path: Path to the image file
            effect_config: Configuration for visual effects. Supported effects:
                - Ken Burns (zoom): {"effect": "ken_burns", "zoom_factor": 0.001, "direction": "zoom-to-top-left"}
                - Pan: {"effect": "pan", "direction": "left-to-right", "speed": "normal"}
        """
        self.background = {
            "type": "image",
            "file": file_path,
            "effect_config": effect_config or {"effect": "ken_burns"},  # Default to Ken Burns for backward compatibility
        }
        return self

    def set_background_video(self, file_path: str):
        """Set background as a video file."""
        self.background = {"type": "video", "file": file_path}
        return self

    def set_audio(self, file_path: str):
        """Set audio file."""
        self.audio_file = file_path
        return self

    def set_captions(
        self,
        file_path: str = None,
        config: dict = None,
    ):
        """Set caption subtitles

        Args:
            file_path: Path to subtitle file
            config: Optional configuration dict
        """
        self.captions = {
            "file": file_path,
            **(config or {}),
        }
        return self

    def set_output_path(self, output_path: str):
        """Set output file path."""
        self.output_path = output_path
        return self

    async def build_command(self):
        """Build the complete FFmpeg command."""
        if not self.background:
            raise ValueError("Background must be set (image or video).")

        if not self.audio_file and not self.captions:
            raise ValueError(
                "At least one of audio_file, or captions must be provided."
            )

        # Validate combinations
        if self.background["type"] == "image" and not self.audio_file:
            raise ValueError("Audio file must be provided if background is an image.")

        if (
            self.background["type"] == "video"
            and not self.audio_file
            and self.captions is None
        ):
            raise ValueError(
                "Audio file or captions must be provided if background is a video."
            )

        # Get audio duration if audio file is provided
        audio_duration = None
        if self.audio_file:
            media_info = await self.media_utils.get_audio_info(self.audio_file)
            audio_duration = media_info.get("duration")
            if not audio_duration:
                raise ValueError("Could not determine audio duration")

        # Build command
        cmd = [self.ffmpeg_path, "-y"]

        filter_parts = []
        input_index = 0

        # Add background input
        if self.background["type"] == "image":
            cmd.extend(
                ["-loop", "1", "-t", str(audio_duration), "-i", self.background["file"]]
            )

            # Get effect configuration with backward compatibility
            effect_config = self.background.get("effect_config", {"effect": "ken_burns"})

            # Handle backward compatibility for old ken_burns config
            if "ken_burns" in self.background and "effect_config" not in self.background:
                # Old format: {"ken_burns": {"zoom_factor": 0.001, "direction": "zoom-to-top-left"}}
                old_ken_burns = self.background.get("ken_burns", {})
                effect_config = {
                    "effect": "ken_burns",
                    "zoom_factor": old_ken_burns.get("zoom_factor", 0.001),
                    "direction": old_ken_burns.get("direction", "zoom-to-top-left")
                }

            effect_type = effect_config.get("effect", "ken_burns")

            fps = 25
            duration_frames = int(audio_duration * fps)

            if effect_type == "ken_burns":
                # Ken Burns (zoom) effect
                zoom_factor = effect_config.get("zoom_factor", 0.001)
                direction = effect_config.get("direction", "zoom-to-top-left")

                zoom_expressions = {
                    "zoom-to-top": f"z='zoom+{zoom_factor}':x=iw/2-(iw/zoom/2):y=0",
                    "zoom-to-center": f"z='zoom+{zoom_factor}':x=iw/2-(iw/zoom/2):y=ih/2-(ih/zoom/2)",
                    "zoom-to-top-left": f"z='zoom+{zoom_factor}':x=0:y=0",
                }
                zoom_expr = zoom_expressions.get(direction, zoom_expressions["zoom-to-top-left"])

                zoompan_d = duration_frames + 1
                filter_parts.append(
                    f"[{input_index}]scale={self.width}:-2,setsar=1:1,"
                    f"crop={self.width}:{self.height},"
                    f"zoompan={zoom_expr}:d={zoompan_d}:s={self.width}x{self.height}:fps={fps}[bg]"
                )

            elif effect_type == "pan":
                # Pan effect - camera moves across the image
                direction = effect_config.get("direction", "left-to-right")
                speed = effect_config.get("speed", "normal")

                # Speed multipliers
                speed_multipliers = {
                    "slow": 0.5,
                    "normal": 1.0,
                    "fast": 2.0
                }
                speed_mult = speed_multipliers.get(speed, 1.0)

                # Calculate pan distance based on direction
                scale_factor = 1.3  # Scale image 30% larger to allow room for panning
                scaled_width = int(self.width * scale_factor)
                scaled_height = int(self.height * scale_factor)

                # Pan expressions for different directions
                if direction == "left-to-right":
                    start_x = 0
                    end_x = scaled_width - self.width
                    start_y = (scaled_height - self.height) // 2
                    end_y = start_y
                elif direction == "right-to-left":
                    start_x = scaled_width - self.width
                    end_x = 0
                    start_y = (scaled_height - self.height) // 2
                    end_y = start_y
                elif direction == "top-to-bottom":
                    start_x = (scaled_width - self.width) // 2
                    end_x = start_x
                    start_y = 0
                    end_y = scaled_height - self.height
                else:  # bottom-to-top
                    start_x = (scaled_width - self.width) // 2
                    end_x = start_x
                    start_y = scaled_height - self.height
                    end_y = 0

                # Calculate movement per frame
                total_frames = duration_frames
                x_step = (end_x - start_x) / total_frames * speed_mult if total_frames > 0 else 0
                y_step = (end_y - start_y) / total_frames * speed_mult if total_frames > 0 else 0

                filter_parts.append(
                    f"[{input_index}]scale={scaled_width}:-2,setsar=1:1,"
                    f"crop={self.width}:{self.height}:x='min(max(0,{start_x}+{x_step}*t*{fps}),{scaled_width - self.width})':y='min(max(0,{start_y}+{y_step}*t*{fps}),{scaled_height - self.height})',fps={fps}[bg]"
                )
            else:
                # No effect, just scale and crop
                filter_parts.append(f"[{input_index}]scale={self.width}:{self.height},setsar=1:1[bg]")

        elif self.background["type"] == "video":
            cmd.extend(["-i", self.background["file"]])
            filter_parts.append(f"[{input_index}]scale={self.width}:{self.height}[bg]")

        input_index += 1
        current_video = "[bg]"

        # Add audio input
        audio_input_index = None
        if self.audio_file:
            cmd.extend(["-i", self.audio_file])
            audio_input_index = input_index
            input_index += 1

        # Add captions input
        captions_input_index = None
        if self.captions and self.captions.get("file"):
            # For subtitle files (ASS, SRT, etc.), use the subtitles filter instead of treating as video input
            captions_file = self.captions["file"]
            if captions_file.lower().endswith(('.ass', '.srt', '.vtt')):
                # Use subtitles filter - don't add as input
                pass
            else:
                # For video caption files, add as input
                cmd.extend(["-i", self.captions["file"]])
                captions_input_index = input_index
                input_index += 1

        # Build filter complex
        filter_complex_parts = []

        # Add background filter
        filter_complex_parts.extend(filter_parts)

        # Add captions overlay if provided
        if self.captions and self.captions.get("file"):
            captions_file = self.captions["file"]
            if captions_file.lower().endswith(('.ass', '.srt', '.vtt')):
                # Use subtitles filter for subtitle files
                filter_complex_parts.append(
                    f"{current_video}subtitles={captions_file}[video_with_captions]"
                )
                current_video = "[video_with_captions]"
            elif captions_input_index is not None:
                # For video caption files, overlay
                filter_complex_parts.append(
                    f"{current_video}[{captions_input_index}]overlay[video_with_captions]"
                )
                current_video = "[video_with_captions]"

        # Set final video output
        if current_video != "[bg]":
            cmd.extend(["-filter_complex", ";".join(filter_complex_parts), "-map", current_video])
        else:
            cmd.extend(["-filter_complex", ";".join(filter_complex_parts), "-map", "[bg]"])

        # Add audio mapping
        if audio_input_index is not None:
            cmd.extend(["-map", f"{audio_input_index}:a"])

        # Add output options
        cmd.extend(["-c:v", "libx264", "-preset", "fast", "-crf", "23", "-c:a", "aac", self.output_path])

        return cmd

    async def execute(self):
        """Execute the built FFmpeg command."""
        cmd = await self.build_command()
        logger.info(f"Executing FFmpeg command: {' '.join(cmd)}")

        import subprocess
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error(f"FFmpeg command failed: {result.stderr}")
            raise RuntimeError(f"FFmpeg command failed: {result.stderr}")

        logger.info("FFmpeg command completed successfully")
        return True