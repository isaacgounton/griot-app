"""
Image enhancement service for removing AI artifacts and adding natural imperfections.
"""
import logging
import os
import tempfile
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
from typing import Dict, Any
from pydantic import AnyUrl
from app.utils.media import download_media_file
from app.models import ImageEnhancementResult

logger = logging.getLogger(__name__)


class ImageEnhancementService:
    """Service for enhancing images by removing AI artifacts and adding natural imperfections."""
    
    async def enhance_image(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance an image by removing AI artifacts and adding natural imperfections.
        
        Args:
            params: Dictionary containing:
                - image_url: URL of the image to enhance
                - enhance_color: Color enhancement strength (0.0-2.0)
                - enhance_contrast: Contrast enhancement strength (0.0-2.0)
                - noise_strength: Noise/grain strength (0-100)
                - remove_artifacts: Apply AI artifact removal
                - add_film_grain: Add film grain effect
                - vintage_effect: Vintage/analog effect strength (0.0-1.0)
                - output_format: Output format
                - output_quality: Quality for lossy formats
                
        Returns:
            Dictionary with result information
        """
        temp_dir = None
        try:
            # Create temp directory
            temp_dir = tempfile.mkdtemp()
            
            # Download the image
            image_url = params["image_url"]
            logger.info(f"Downloading image from: {image_url}")
            
            local_image_path, _ = await download_media_file(image_url, temp_dir)
            
            # Load image
            with Image.open(local_image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                original_size = img.size
                logger.info(f"Processing image: {original_size[0]}x{original_size[1]}")
                
                # Apply enhancements
                enhanced_img = await self._apply_enhancements(img, params)
                
                # Save enhanced image
                output_format = params.get("output_format", "png").lower()
                output_quality = params.get("output_quality", 90)
                
                enhanced_filename = f"enhanced_{os.path.basename(local_image_path)}"
                if not enhanced_filename.lower().endswith(f".{output_format}"):
                    enhanced_filename = f"{os.path.splitext(enhanced_filename)[0]}.{output_format}"
                
                enhanced_path = os.path.join(temp_dir, enhanced_filename)
                
                # Save with appropriate settings
                save_kwargs = {"format": output_format.upper()}
                if output_format.lower() in ["jpg", "jpeg"]:
                    save_kwargs["quality"] = output_quality
                    save_kwargs["optimize"] = True
                elif output_format.lower() == "png":
                    save_kwargs["optimize"] = True
                elif output_format.lower() == "webp":
                    save_kwargs["quality"] = output_quality
                    save_kwargs["optimize"] = True
                
                enhanced_img.save(enhanced_path, **save_kwargs)
                
                # Get file sizes
                original_size_bytes = os.path.getsize(local_image_path)
                enhanced_size_bytes = os.path.getsize(enhanced_path)
                
                # Upload to S3
                from app.services.s3.s3 import s3_service
                s3_key = f"enhanced_images/{enhanced_filename}"
                s3_url = await s3_service.upload_file(enhanced_path, s3_key)
                
                # Get applied enhancements
                enhancements_applied = self._get_applied_enhancements(params)
                
                # Create result
                result = ImageEnhancementResult(
                    image_url=AnyUrl(s3_url),
                    storage_path=s3_key,
                    width=enhanced_img.width,
                    height=enhanced_img.height,
                    format=output_format,
                    enhancements_applied=enhancements_applied,
                    original_size_bytes=original_size_bytes,
                    enhanced_size_bytes=enhanced_size_bytes
                )
                
                logger.info(f"Image enhancement completed. Size: {enhanced_img.width}x{enhanced_img.height}")
                logger.info(f"Enhancements applied: {', '.join(enhancements_applied)}")
                
                return result.dict()
                
        except Exception as e:
            logger.error(f"Error enhancing image: {str(e)}")
            raise
        finally:
            # Clean up temp directory
            if temp_dir and os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    async def _apply_enhancements(self, img: Image.Image, params: Dict[str, Any]) -> Image.Image:
        """Apply various enhancements to the image."""
        enhanced_img = img.copy()
        
        # 1. Remove AI artifacts (subtle unsharp mask to add texture)
        if params.get("remove_artifacts", True):
            enhanced_img = self._remove_ai_artifacts(enhanced_img)
        
        # 2. Adjust color enhancement
        enhance_color = params.get("enhance_color", 1.0)
        if enhance_color != 1.0:
            color_enhancer = ImageEnhance.Color(enhanced_img)
            enhanced_img = color_enhancer.enhance(enhance_color)
        
        # 3. Adjust contrast
        enhance_contrast = params.get("enhance_contrast", 1.0)
        if enhance_contrast != 1.0:
            contrast_enhancer = ImageEnhance.Contrast(enhanced_img)
            enhanced_img = contrast_enhancer.enhance(enhance_contrast)
        
        # 4. Add noise for natural imperfections
        noise_strength = params.get("noise_strength", 10)
        if noise_strength > 0:
            enhanced_img = self._add_noise(enhanced_img, noise_strength)
        
        # 5. Add film grain effect
        if params.get("add_film_grain", False):
            enhanced_img = self._add_film_grain(enhanced_img)
        
        # 6. Apply vintage effect
        vintage_strength = params.get("vintage_effect", 0.0)
        if vintage_strength > 0:
            enhanced_img = self._apply_vintage_effect(enhanced_img, vintage_strength)
        
        return enhanced_img
    
    def _remove_ai_artifacts(self, img: Image.Image) -> Image.Image:
        """Remove AI artifacts by adding subtle texture and reducing over-smoothing."""
        # Apply a very subtle unsharp mask to add back texture
        # This helps counteract the over-smoothing common in AI-generated images
        blurred = img.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        # Convert to numpy for pixel-level operations
        img_array = np.array(img)
        blurred_array = np.array(blurred)
        
        # Subtle unsharp mask (amount=0.3, threshold=2)
        mask = img_array - blurred_array
        enhanced_array = img_array + 0.3 * mask
        
        # Clamp values
        enhanced_array = np.clip(enhanced_array, 0, 255)
        
        return Image.fromarray(enhanced_array.astype(np.uint8))
    
    def _add_noise(self, img: Image.Image, strength: int) -> Image.Image:
        """Add subtle noise to make the image look more natural."""
        img_array = np.array(img)
        
        # Generate noise
        noise = np.random.normal(0, strength * 0.5, img_array.shape)
        
        # Add noise to image
        noisy_array = img_array + noise
        
        # Clamp values
        noisy_array = np.clip(noisy_array, 0, 255)
        
        return Image.fromarray(noisy_array.astype(np.uint8))
    
    def _add_film_grain(self, img: Image.Image) -> Image.Image:
        """Add film grain effect for analog look."""
        img_array = np.array(img)
        
        # Create film grain pattern
        grain = np.random.random(img_array.shape) * 10 - 5
        
        # Apply grain more to darker areas
        brightness = np.mean(img_array, axis=2, keepdims=True) / 255.0
        grain_mask = 1.0 - brightness * 0.7  # Less grain in bright areas
        
        grain = grain * grain_mask
        
        # Add grain to image
        grained_array = img_array + grain
        
        # Clamp values
        grained_array = np.clip(grained_array, 0, 255)
        
        return Image.fromarray(grained_array.astype(np.uint8))
    
    def _apply_vintage_effect(self, img: Image.Image, strength: float) -> Image.Image:
        """Apply vintage/analog color effect."""
        img_array = np.array(img, dtype=np.float32)
        
        # Vintage color matrix (warm tones, slight yellow/orange cast)
        vintage_matrix = np.array([
            [1.0 + strength * 0.1, strength * 0.05, -strength * 0.02],
            [-strength * 0.02, 1.0, strength * 0.08],
            [-strength * 0.05, -strength * 0.1, 1.0 + strength * 0.15]
        ])
        
        # Apply color transformation
        vintage_array = np.dot(img_array, vintage_matrix.T)
        
        # Add slight vignette effect
        h, w = img_array.shape[:2]
        center_x, center_y = w // 2, h // 2
        
        y, x = np.ogrid[:h, :w]
        distance = np.sqrt((x - center_x)**2 + (y - center_y)**2)
        max_distance = np.sqrt(center_x**2 + center_y**2)
        
        vignette = 1.0 - (distance / max_distance) * strength * 0.3
        vignette = np.clip(vignette, 0.7, 1.0)
        
        vintage_array = vintage_array * vignette[:, :, np.newaxis]
        
        # Clamp values
        vintage_array = np.clip(vintage_array, 0, 255)
        
        return Image.fromarray(vintage_array.astype(np.uint8))
    
    def _get_applied_enhancements(self, params: Dict[str, Any]) -> list[str]:
        """Get list of enhancements that were applied."""
        enhancements = []
        
        if params.get("remove_artifacts", True):
            enhancements.append("AI artifact removal")
        
        enhance_color = params.get("enhance_color", 1.0)
        if enhance_color != 1.0:
            if enhance_color < 1.0:
                enhancements.append("Color desaturation")
            else:
                enhancements.append("Color enhancement")
        
        enhance_contrast = params.get("enhance_contrast", 1.0)
        if enhance_contrast != 1.0:
            if enhance_contrast < 1.0:
                enhancements.append("Contrast reduction")
            else:
                enhancements.append("Contrast enhancement")
        
        noise_strength = params.get("noise_strength", 10)
        if noise_strength > 0:
            enhancements.append("Natural noise addition")
        
        if params.get("add_film_grain", False):
            enhancements.append("Film grain effect")
        
        vintage_strength = params.get("vintage_effect", 0.0)
        if vintage_strength > 0:
            enhancements.append("Vintage/analog effect")
        
        return enhancements


# Create service instance
image_enhancement_service = ImageEnhancementService()