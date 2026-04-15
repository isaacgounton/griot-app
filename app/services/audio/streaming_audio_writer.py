"""
Streaming audio writer for real-time format conversion.
"""
import io
import struct
from typing import Optional
import numpy as np
import logging

# Optional dependency - FFmpeg functionality  
try:
    import av
    FFMPEG_AVAILABLE = True
except ImportError:
    FFMPEG_AVAILABLE = False

logger = logging.getLogger(__name__)


class StreamingAudioWriter:
    """Handles streaming audio format conversions."""
    
    def __init__(self, format: str, sample_rate: int = 24000, channels: int = 1):
        self.format = format.lower()
        self.sample_rate = sample_rate
        self.channels = channels
        self.bytes_written = 0
        self.pts = 0
        self.container = None
        self.stream = None
        self.output_buffer = None
        
        if self.format == "pcm":
            # PCM doesn't need a container
            pass
        elif self.format == "wav":
            # WAV can be handled without FFmpeg
            self.output_buffer = io.BytesIO()
            self._write_wav_header()
        elif FFMPEG_AVAILABLE and self.format in ["mp3", "opus", "aac", "flac"]:
            self._init_ffmpeg_writer()
        else:
            if not FFMPEG_AVAILABLE:
                logger.warning(f"FFmpeg not available, falling back to WAV for {self.format}")
                self.format = "wav"
                self.output_buffer = io.BytesIO()
                self._write_wav_header()
            else:
                raise ValueError(f"Unsupported format: {self.format}")
    
    def _write_wav_header(self):
        """Write WAV header to output buffer."""
        # WAV header for 16-bit PCM
        self.output_buffer.write(b'RIFF')
        self.output_buffer.write(struct.pack('<I', 0))  # File size placeholder
        self.output_buffer.write(b'WAVE')
        self.output_buffer.write(b'fmt ')
        self.output_buffer.write(struct.pack('<I', 16))  # fmt chunk size
        self.output_buffer.write(struct.pack('<H', 1))   # PCM format
        self.output_buffer.write(struct.pack('<H', self.channels))
        self.output_buffer.write(struct.pack('<I', self.sample_rate))
        self.output_buffer.write(struct.pack('<I', self.sample_rate * self.channels * 2))  # byte rate
        self.output_buffer.write(struct.pack('<H', self.channels * 2))  # block align
        self.output_buffer.write(struct.pack('<H', 16))  # bits per sample
        self.output_buffer.write(b'data')
        self.output_buffer.write(struct.pack('<I', 0))  # Data size placeholder
    
    def _init_ffmpeg_writer(self):
        """Initialize FFmpeg-based writer."""
        if not FFMPEG_AVAILABLE:
            raise RuntimeError("FFmpeg not available")
        
        codec_map = {
            "mp3": "mp3",
            "opus": "libopus", 
            "flac": "flac",
            "aac": "aac",
        }
        
        self.output_buffer = io.BytesIO()
        container_options = {}
        
        # MP3-specific options
        if self.format == 'mp3':
            container_options = {'write_xing': '0'}  # Disable Xing VBR header
        
        self.container = av.open(
            self.output_buffer,
            mode="w",
            format=self.format if self.format != "aac" else "adts",
            options=container_options
        )
        
        self.stream = self.container.add_stream(
            codec_map[self.format],
            rate=self.sample_rate,
            layout="mono" if self.channels == 1 else "stereo",
        )
        
        # Set bitrate for compressed formats
        if self.format in ['mp3', 'aac', 'opus']:
            self.stream.bit_rate = 128000
    
    def write_chunk(self, audio_data: Optional[np.ndarray] = None, finalize: bool = False) -> bytes:
        """
        Write audio chunk and return formatted bytes.
        
        Args:
            audio_data: Audio data to write (int16 numpy array)
            finalize: Whether this is the final write
            
        Returns:
            Formatted audio bytes
        """
        if finalize:
            return self._finalize()
        
        if audio_data is None or len(audio_data) == 0:
            return b""
        
        # Ensure audio is int16
        if audio_data.dtype != np.int16:
            audio_data = (audio_data * 32767).astype(np.int16)
        
        if self.format == "pcm":
            return audio_data.tobytes()
        elif self.format == "wav":
            return self._write_wav_chunk(audio_data)
        elif FFMPEG_AVAILABLE and hasattr(self, 'container'):
            return self._write_ffmpeg_chunk(audio_data)
        else:
            # Fallback to WAV
            return self._write_wav_chunk(audio_data)
    
    def _write_wav_chunk(self, audio_data: np.ndarray) -> bytes:
        """Write chunk to WAV buffer."""
        chunk_data = audio_data.tobytes()
        self.output_buffer.write(chunk_data)
        self.bytes_written += len(chunk_data)
        return chunk_data
    
    def _write_ffmpeg_chunk(self, audio_data: np.ndarray) -> bytes:
        """Write chunk using FFmpeg."""
        try:
            # Convert to float32 for FFmpeg
            if audio_data.dtype == np.int16:
                audio_float = audio_data.astype(np.float32) / 32767.0
            else:
                audio_float = audio_data.astype(np.float32)
            
            frame = av.AudioFrame.from_ndarray(
                audio_float.reshape(1, -1),
                format='fltp',
                layout='mono' if self.channels == 1 else 'stereo'
            )
            frame.pts = self.pts
            frame.sample_rate = self.sample_rate
            
            packets = self.stream.encode(frame)
            output_data = b""
            
            for packet in packets:
                self.container.mux(packet)
                # Get current buffer content
                current_pos = self.output_buffer.tell()
                self.output_buffer.seek(0)
                current_data = self.output_buffer.read()
                self.output_buffer.seek(current_pos)
                
                # Return new data since last write
                if len(current_data) > self.bytes_written:
                    new_data = current_data[self.bytes_written:]
                    self.bytes_written = len(current_data)
                    output_data += new_data
            
            self.pts += len(audio_data)
            return output_data
            
        except Exception as e:
            logger.error(f"FFmpeg encoding error: {e}")
            # Fallback to WAV
            return self._write_wav_chunk(audio_data)
    
    def _finalize(self) -> bytes:
        """Finalize the audio stream and return any remaining bytes."""
        if self.format == "pcm":
            return b""
        elif self.format == "wav":
            return self._finalize_wav()
        elif FFMPEG_AVAILABLE and hasattr(self, 'container'):
            return self._finalize_ffmpeg()
        else:
            return self._finalize_wav()
    
    def _finalize_wav(self) -> bytes:
        """Finalize WAV file by updating headers."""
        if not self.output_buffer:
            return b""
        
        # Update file size in header
        current_pos = self.output_buffer.tell()
        self.output_buffer.seek(4)
        self.output_buffer.write(struct.pack('<I', current_pos - 8))  # File size
        self.output_buffer.seek(40)
        self.output_buffer.write(struct.pack('<I', self.bytes_written))  # Data size
        self.output_buffer.seek(current_pos)
        
        # Return complete WAV file
        self.output_buffer.seek(0)
        complete_data = self.output_buffer.read()
        return complete_data
    
    def _finalize_ffmpeg(self) -> bytes:
        """Finalize FFmpeg stream."""
        try:
            # Flush encoder
            packets = self.stream.encode(None)
            for packet in packets:
                self.container.mux(packet)
            
            # Get final data
            self.output_buffer.seek(0)
            final_data = self.output_buffer.read()
            return final_data
            
        except Exception as e:
            logger.error(f"FFmpeg finalization error: {e}")
            return b""
    
    def close(self):
        """Close the writer and cleanup resources."""
        if hasattr(self, 'container') and self.container:
            try:
                self.container.close()
            except:
                pass
        
        if hasattr(self, 'output_buffer') and self.output_buffer:
            try:
                self.output_buffer.close()
            except:
                pass