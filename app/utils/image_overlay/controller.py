"""
Controller for image overlay processing.

This module orchestrates the process of overlaying images on a base image.
"""
import os
import logging
import uuid
from typing import Dict, Any, List
import asyncio
from PIL import Image, ImageEnhance

from app.utils.media import download_media_file
from app.services.s3.s3 import s3_service
from app.utils.image_overlay.image_processing import process_overlay_image
from app.utils.image_to_video.image_processing import process_image

# Configure logging
logger = logging.getLogger(__name__)

async def process_image_overlay(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process the overlay of images on top of a base image.
    
    Args:
        params: Dict containing the following keys:
            - base_image_url: URL of the base image
            - overlay_images: List of overlay images with position information
            - output_format: Output image format (e.g., 'png', 'jpg', 'webp')
            - output_quality: Quality for lossy formats (1-100)
            - output_width: Width of the output image (optional)
            - output_height: Height of the output image (optional)
            - maintain_aspect_ratio: Whether to maintain the aspect ratio when resizing
    
    Returns:
        Dict containing the result information
    """
    try:
        # Generate a unique identifier for this job
        job_id = str(uuid.uuid4())
        temp_dir = os.path.join("temp", job_id)
        os.makedirs(temp_dir, exist_ok=True)
        
        # Download base image using process_image from image_to_video utilities
        logger.info(f"Downloading base image from {params['base_image_url']}")
        base_image_result = await process_image(params['base_image_url'])
        base_image_path = base_image_result['image_path']
        
        # Load the base image
        base_image = Image.open(base_image_path).convert("RGBA")
        
        # Get original dimensions
        original_width, original_height = base_image.size
        logger.info(f"Base image dimensions: {original_width}x{original_height}")
        
        # Process overlay images
        overlay_images = params['overlay_images']
        
        # Check if stitching mode is enabled
        stitch_mode = params.get('stitch_mode', False)
        
        if stitch_mode:
            # Stitch images together
            base_image = await process_image_stitching(base_image, overlay_images, params, temp_dir)
        else:
            # Sort overlay images by z-index
            overlay_images = sorted(overlay_images, key=lambda x: x.get('z_index', 0))
            
            # Apply each overlay
            for overlay_info in overlay_images:
                # Process one overlay at a time
                base_image = await process_overlay_image(base_image, overlay_info, temp_dir)
        
        # Apply any resizing if specified
        output_width = params.get('output_width')
        output_height = params.get('output_height')
        maintain_aspect_ratio = params.get('maintain_aspect_ratio', True)
        
        if output_width or output_height:
            if maintain_aspect_ratio:
                # Calculate dimensions maintaining aspect ratio
                if output_width and not output_height:
                    output_height = int(original_height * (output_width / original_width))
                elif output_height and not output_width:
                    output_width = int(original_width * (output_height / original_height))
            
            # Resize the image
            if output_width and output_height:
                logger.info(f"Resizing output image to {output_width}x{output_height}")
                base_image = base_image.resize((output_width, output_height), Image.LANCZOS)
        
        # Save the result image
        output_format = params.get('output_format', 'png').upper()
        if output_format == 'JPG':
            output_format = 'JPEG'  # PIL uses JPEG, not JPG
        
        output_quality = params.get('output_quality', 90)
        
        # Convert to RGB if saving as JPEG (which doesn't support alpha)
        if output_format == 'JPEG':
            # Create a white background
            white_bg = Image.new('RGB', base_image.size, (255, 255, 255))
            # Paste the image with alpha onto the white background
            white_bg.paste(base_image, (0, 0), base_image)
            base_image = white_bg
        
        # Save the result to a temporary file
        output_filename = f"{job_id}.{output_format.lower()}"
        output_path = os.path.join(temp_dir, output_filename)
        
        # Save with quality parameter for JPEG
        if output_format == 'JPEG':
            base_image.save(output_path, format=output_format, quality=output_quality)
        else:
            base_image.save(output_path, format=output_format)
        
        # Upload the result to S3
        logger.info(f"Uploading result image to storage")
        s3_path = f"image-overlay-results/{output_filename}"
        result_url = await s3_service.upload_file(output_path, s3_path)
        
        # Remove signature parameters from URL if present
        if '?' in result_url:
            result_url = result_url.split('?')[0]
        
        # Get final dimensions
        final_width, final_height = base_image.size
        
        # Return the result
        result = {
            "image_url": result_url,
            "width": final_width,
            "height": final_height,
            "format": output_format.lower(),
            "storage_path": s3_path
        }
        
        # Clean up temporary files
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except Exception as e:
            logger.warning(f"Failed to clean up temporary files: {str(e)}")
        
        return result
    
    except Exception as e:
        logger.error(f"Error in process_image_overlay: {str(e)}", exc_info=True)
        raise 


async def process_image_stitching(base_image: Image.Image, overlay_images: List[Dict[str, Any]], params: Dict[str, Any], temp_dir: str) -> Image.Image:
    """
    Stitch images together instead of overlaying them.
    
    Args:
        base_image: The base image
        overlay_images: List of overlay images to stitch
        params: Parameters including stitching options
        temp_dir: Temporary directory for processing
        
    Returns:
        Stitched image
    """
    try:
        # Download all overlay images
        all_images = [base_image]
        
        for overlay_info in overlay_images:
            image_url = overlay_info['url']
            logger.info(f"Downloading overlay image from {image_url}")
            image_path = await download_media_file(image_url, temp_dir)
            overlay_image = Image.open(image_path).convert("RGBA")
            all_images.append(overlay_image)
        
        # Get stitching parameters
        stitch_direction = params.get('stitch_direction', 'horizontal')
        stitch_spacing = params.get('stitch_spacing', 0)
        stitch_max_width = params.get('stitch_max_width', 1920)
        stitch_max_height = params.get('stitch_max_height', 1080)
        
        logger.info(f"Stitching {len(all_images)} images in {stitch_direction} direction with {stitch_spacing}px spacing")
        
        if stitch_direction == 'horizontal':
            return await stitch_images_horizontal(all_images, stitch_spacing, stitch_max_width, stitch_max_height)
        elif stitch_direction == 'vertical':
            return await stitch_images_vertical(all_images, stitch_spacing, stitch_max_width, stitch_max_height)
        elif stitch_direction == 'grid':
            return await stitch_images_grid(all_images, stitch_spacing, stitch_max_width, stitch_max_height)
        else:
            raise ValueError(f"Unsupported stitch direction: {stitch_direction}")
            
    except Exception as e:
        logger.error(f"Error in process_image_stitching: {str(e)}")
        raise


async def stitch_images_horizontal(images: List[Image.Image], spacing: int, max_width: int, max_height: int) -> Image.Image:
    """Stitch images horizontally."""
    if not images:
        raise ValueError("No images to stitch")
    
    # Calculate uniform height (use the height of the smallest image to fit all)
    min_height = min(img.size[1] for img in images)
    
    # Resize all images to the same height while maintaining aspect ratio
    resized_images = []
    total_width = 0
    
    for img in images:
        if img.size[1] != min_height:
            # Calculate new width maintaining aspect ratio
            new_width = int(img.size[0] * (min_height / img.size[1]))
            img = img.resize((new_width, min_height), Image.LANCZOS)
        
        resized_images.append(img)
        total_width += img.size[0]
    
    # Add spacing
    total_width += spacing * (len(images) - 1)
    
    # Check if we need to scale down to fit max dimensions
    if total_width > max_width or min_height > max_height:
        scale_factor = min(max_width / total_width, max_height / min_height)
        
        scaled_images = []
        total_width = 0
        min_height = int(min_height * scale_factor)
        
        for img in resized_images:
            new_width = int(img.size[0] * scale_factor)
            scaled_img = img.resize((new_width, min_height), Image.LANCZOS)
            scaled_images.append(scaled_img)
            total_width += new_width
        
        total_width += int(spacing * scale_factor) * (len(images) - 1)
        resized_images = scaled_images
        spacing = int(spacing * scale_factor)
    
    # Create the stitched image
    stitched = Image.new('RGBA', (total_width, min_height), (0, 0, 0, 0))
    
    x_offset = 0
    for img in resized_images:
        stitched.paste(img, (x_offset, 0), img if img.mode == 'RGBA' else None)
        x_offset += img.size[0] + spacing
    
    return stitched


async def stitch_images_vertical(images: List[Image.Image], spacing: int, max_width: int, max_height: int) -> Image.Image:
    """Stitch images vertically."""
    if not images:
        raise ValueError("No images to stitch")
    
    # Calculate uniform width (use the width of the smallest image to fit all)
    min_width = min(img.size[0] for img in images)
    
    # Resize all images to the same width while maintaining aspect ratio
    resized_images = []
    total_height = 0
    
    for img in images:
        if img.size[0] != min_width:
            # Calculate new height maintaining aspect ratio
            new_height = int(img.size[1] * (min_width / img.size[0]))
            img = img.resize((min_width, new_height), Image.LANCZOS)
        
        resized_images.append(img)
        total_height += img.size[1]
    
    # Add spacing
    total_height += spacing * (len(images) - 1)
    
    # Check if we need to scale down to fit max dimensions
    if min_width > max_width or total_height > max_height:
        scale_factor = min(max_width / min_width, max_height / total_height)
        
        scaled_images = []
        total_height = 0
        min_width = int(min_width * scale_factor)
        
        for img in resized_images:
            new_height = int(img.size[1] * scale_factor)
            scaled_img = img.resize((min_width, new_height), Image.LANCZOS)
            scaled_images.append(scaled_img)
            total_height += new_height
        
        total_height += int(spacing * scale_factor) * (len(images) - 1)
        resized_images = scaled_images
        spacing = int(spacing * scale_factor)
    
    # Create the stitched image
    stitched = Image.new('RGBA', (min_width, total_height), (0, 0, 0, 0))
    
    y_offset = 0
    for img in resized_images:
        stitched.paste(img, (0, y_offset), img if img.mode == 'RGBA' else None)
        y_offset += img.size[1] + spacing
    
    return stitched


async def stitch_images_grid(images: List[Image.Image], spacing: int, max_width: int, max_height: int) -> Image.Image:
    """Stitch images in a grid layout."""
    if not images:
        raise ValueError("No images to stitch")
    
    num_images = len(images)
    
    # Calculate grid dimensions (try to make it as square as possible)
    cols = int(num_images ** 0.5)
    rows = (num_images + cols - 1) // cols  # Ceiling division
    
    # If we have extra space, distribute it
    if cols * rows > num_images:
        if cols > rows:
            cols = (num_images + rows - 1) // rows
        else:
            rows = (num_images + cols - 1) // cols
    
    logger.info(f"Creating {rows}x{cols} grid for {num_images} images")
    
    # Calculate cell size (accounting for spacing)
    available_width = max_width - (spacing * (cols - 1))
    available_height = max_height - (spacing * (rows - 1))
    
    cell_width = available_width // cols
    cell_height = available_height // rows
    
    # Resize all images to fit in cells while maintaining aspect ratio
    resized_images = []
    for img in images:
        # Calculate scale factor to fit in cell
        scale_factor = min(cell_width / img.size[0], cell_height / img.size[1])
        
        new_width = int(img.size[0] * scale_factor)
        new_height = int(img.size[1] * scale_factor)
        
        resized_img = img.resize((new_width, new_height), Image.LANCZOS)
        resized_images.append(resized_img)
    
    # Calculate actual grid size
    grid_width = cols * cell_width + spacing * (cols - 1)
    grid_height = rows * cell_height + spacing * (rows - 1)
    
    # Create the grid image
    stitched = Image.new('RGBA', (grid_width, grid_height), (0, 0, 0, 0))
    
    # Place images in grid
    for i, img in enumerate(resized_images):
        row = i // cols
        col = i % cols
        
        # Calculate position (center image in cell)
        x = col * (cell_width + spacing) + (cell_width - img.size[0]) // 2
        y = row * (cell_height + spacing) + (cell_height - img.size[1]) // 2
        
        stitched.paste(img, (x, y), img if img.mode == 'RGBA' else None)
    
    return stitched