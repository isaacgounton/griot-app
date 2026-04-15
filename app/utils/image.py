"""
Enhanced Image Processing Utilities

Advanced image processing functions ported from AI agents no-code tools.
Provides comprehensive image manipulation capabilities including stitching,
resizing, effects, and text generation.
"""
import os
import uuid
import asyncio
import logging
import math
from typing import List, Tuple, Optional
from io import BytesIO

import numpy as np
import requests
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw, ImageChops, ImageOps, ImageFont

from app.utils.download import download_image

logger = logging.getLogger(__name__)


async def stitch_images(
    image_urls: List[str],
    max_width: int = 1920,
    max_height: int = 1080,
    temp_dir: str = "temp"
) -> str:
    """
    Stitch multiple images into a single image asynchronously.
    Downloads images from URLs, arranges them in a grid, and resizes proportionally to fit max dimensions.

    Args:
        image_urls: List of image URLs to download and stitch
        max_width: Maximum width of the final stitched image
        max_height: Maximum height of the final stitched image
        temp_dir: Temporary directory for processing

    Returns:
        S3 URL of the stitched result image
    """
    if not image_urls:
        raise ValueError("No image URLs provided")

    # Download and open all images
    images = []
    for url in image_urls:
        try:
            logger.info(f"Downloading image from {url}")
            image_path = await download_image(url, temp_dir=temp_dir)
            img = Image.open(image_path)
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            images.append(img)
        except Exception as e:
            logger.error(f"Failed to download image from {url}: {e}")
            continue

    if not images:
        raise ValueError("No valid images could be downloaded")

    # Calculate optimal grid dimensions
    num_images = len(images)
    cols = math.ceil(math.sqrt(num_images))
    rows = math.ceil(num_images / cols)

    # Find the maximum dimensions among all images to ensure consistent sizing
    max_img_width = max(img.width for img in images)
    max_img_height = max(img.height for img in images)

    # Calculate the size for each cell in the grid
    cell_width = max_img_width
    cell_height = max_img_height

    # Create the stitched image canvas
    canvas_width = cols * cell_width
    canvas_height = rows * cell_height
    stitched = Image.new('RGB', (canvas_width, canvas_height), color='white')

    # Place images in the grid
    for i, img in enumerate(images):
        row = i // cols
        col = i % cols

        # Calculate position for this image
        x = col * cell_width
        y = row * cell_height

        # Resize image to fit cell while maintaining aspect ratio
        img_resized = resize_image_to_fit(img, cell_width, cell_height)

        # Center the image in the cell
        offset_x = (cell_width - img_resized.width) // 2
        offset_y = (cell_height - img_resized.height) // 2

        stitched.paste(img_resized, (x + offset_x, y + offset_y))

    # Resize the final stitched image to fit within max dimensions
    final_image = resize_image_to_fit(stitched, max_width, max_height)

    # Save and upload to S3
    output_filename = f"stitched_{uuid.uuid4().hex}.jpg"
    output_path = os.path.join(temp_dir, output_filename)
    final_image.save(output_path, format='JPEG', quality=90)

    s3_path = f"image-processing/{output_filename}"
    from app.services.s3.s3 import s3_service
    result_url = await s3_service.upload_file(output_path, s3_path)

    # Clean up
    try:
        os.remove(output_path)
    except Exception as e:
        logger.warning(f"Failed to clean up temporary file: {e}")

    return result_url


async def resize_image_cover(
    image_url: str,
    target_width: int,
    target_height: int,
    temp_dir: str = "temp"
) -> str:
    """
    Resize an image to fill the specified dimensions while maintaining aspect ratio.
    The image is scaled to cover the entire target area and cropped to fit.

    Args:
        image_url: URL or local path of the image to resize
        target_width: Target width
        target_height: Target height
        temp_dir: Temporary directory for processing

    Returns:
        S3 URL of the resized and cropped image
    """
    try:
        # Download or use local image
        if image_url.startswith(('http://', 'https://')):
            image_path = await download_image(image_url, temp_dir=temp_dir)
        else:
            image_path = image_url

        image = Image.open(image_path)

        # Calculate the scaling factor to cover the entire target area
        width_ratio = target_width / image.width
        height_ratio = target_height / image.height
        scale_factor = max(width_ratio, height_ratio)  # Use max to ensure coverage

        # Scale the image
        new_width = int(image.width * scale_factor)
        new_height = int(image.height * scale_factor)
        scaled_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Calculate crop box to center the image
        left = (new_width - target_width) // 2
        top = (new_height - target_height) // 2
        right = left + target_width
        bottom = top + target_height

        # Crop the image to the target dimensions
        cropped_image = scaled_image.crop((left, top, right, bottom))

        # Convert to RGB if the image has transparency (RGBA mode)
        if cropped_image.mode == 'RGBA':
            # Create a white background and paste the image on it
            rgb_image = Image.new('RGB', cropped_image.size, (255, 255, 255))
            rgb_image.paste(cropped_image, mask=cropped_image.split()[-1])  # Use alpha channel as mask
            cropped_image = rgb_image

        # Save and upload
        output_filename = f"resized_cover_{uuid.uuid4().hex}.jpg"
        output_path = os.path.join(temp_dir, output_filename)
        cropped_image.save(output_path, format='JPEG', quality=90)

        s3_path = f"image-processing/{output_filename}"
        from app.services.s3.s3 import s3_service
        result_url = await s3_service.upload_file(output_path, s3_path)

        # Clean up
        try:
            os.remove(output_path)
        except Exception as e:
            logger.warning(f"Failed to clean up temporary file: {e}")

        return result_url

    except Exception as e:
        logger.error(f"Failed to resize image cover: {e}")
        raise


def resize_image_to_fit(image: Image.Image, max_width: int, max_height: int) -> Image.Image:
    """
    Resize an image to fit within the specified dimensions while maintaining aspect ratio.

    Args:
        image: PIL Image object to resize
        max_width: Maximum width
        max_height: Maximum height

    Returns:
        Resized PIL Image object
    """
    # Calculate the scaling factor to fit within max dimensions
    width_ratio = max_width / image.width
    height_ratio = max_height / image.height
    scale_factor = min(width_ratio, height_ratio)

    # Only resize if the image is larger than max dimensions
    if scale_factor < 1:
        new_width = int(image.width * scale_factor)
        new_height = int(image.height * scale_factor)
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    return image


async def make_image_imperfect(
    image_url: str,
    enhance_color: float = None,
    enhance_contrast: float = None,
    noise_strength: int = 15,
    temp_dir: str = "temp"
) -> str:
    """
    Remove AI-generated artifacts from an image by applying various effects.

    Args:
        image_url: URL or local path of the image to process
        enhance_color: Color enhancement factor
        enhance_contrast: Contrast enhancement factor
        noise_strength: Strength of noise to add
        temp_dir: Temporary directory for processing

    Returns:
        S3 URL of the processed image
    """
    try:
        # Download or use local image
        if image_url.startswith(('http://', 'https://')):
            image_path = await download_image(image_url, temp_dir=temp_dir)
        else:
            image_path = image_url

        img = Image.open(image_path)

        if enhance_color is not None:
            img = ImageEnhance.Color(img).enhance(enhance_color)
        if enhance_contrast is not None:
            img = ImageEnhance.Contrast(img).enhance(enhance_contrast)

        img = img.filter(ImageFilter.SHARPEN)
        img = img.filter(ImageFilter.GaussianBlur(radius=0.5))

        if img.mode != 'RGB':
            img = img.convert('RGB')
        img_array = np.array(img)
        h, w, c = img_array.shape
        grayscale_noise = np.random.randint(-noise_strength, noise_strength + 1, (h, w), dtype='int16')
        noise = np.stack([grayscale_noise] * c, axis=2)
        noisy_array = img_array.astype('int16') + noise
        noisy_array = np.clip(noisy_array, 0, 255).astype('uint8')
        img = Image.fromarray(noisy_array)

        img = cup_of_coffee_tone(img)
        img = chromatic_aberration(img, shift=1)

        # Save and upload
        output_filename = f"imperfect_{uuid.uuid4().hex}.jpg"
        output_path = os.path.join(temp_dir, output_filename)
        img.save(output_path, format='JPEG', quality=90)

        s3_path = f"image-processing/{output_filename}"
        from app.services.s3.s3 import s3_service
        result_url = await s3_service.upload_file(output_path, s3_path)

        # Clean up
        try:
            os.remove(output_path)
        except Exception as e:
            logger.warning(f"Failed to clean up temporary file: {e}")

        return result_url

    except Exception as e:
        logger.error(f"Failed to make image imperfect: {e}")
        raise ValueError("Failed to unaize image") from e


def cup_of_coffee_tone(img):
    """Apply a subtle coffee tone effect to the image."""
    sepia = ImageOps.colorize(img.convert("L"), "#704214", "#C0A080")
    return Image.blend(img, sepia, alpha=0.2)


def chromatic_aberration(img, shift=2):
    """Apply chromatic aberration effect by shifting color channels."""
    r, g, b = img.split()
    # Use transform with AFFINE to shift the channels
    r = r.transform(img.size, Image.AFFINE, (1, 0, -shift, 0, 1, 0))
    b = b.transform(img.size, Image.AFFINE, (1, 0, shift, 0, 1, 0))
    return Image.merge("RGB", (r, g, b))


async def create_text_image(
    text: str,
    size: Tuple[int, int] = (1920, 1080),
    font_size: int = 120,
    font_color: str = "white",
    font_path: str = None,
    temp_dir: str = "temp"
) -> str:
    """
    Create an image with centered text.

    Args:
        text: Text to display on the image
        size: Tuple of (width, height) for the image
        font_size: Size of the font
        font_color: Color of the text
        font_path: Path to font file (optional)
        temp_dir: Temporary directory for processing

    Returns:
        S3 URL of the text image
    """
    img = Image.new('RGB', size, color='black')
    draw = ImageDraw.Draw(img)

    font = ImageFont.load_default(size=font_size)
    if font_path and os.path.exists(font_path):
        font = ImageFont.truetype(font_path, font_size)

    # Handle multi-line text
    lines = text.split('\n')
    total_height = 0
    line_heights = []

    for line in lines:
        bbox = font.getbbox(line)
        line_height = bbox[3] - bbox[1]
        line_heights.append(line_height)
        total_height += line_height

    # Calculate starting Y position to center all lines
    start_y = (size[1] - total_height) // 2
    current_y = start_y

    for i, line in enumerate(lines):
        bbox = font.getbbox(line)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (size[0] - text_width) // 2
        y = current_y
        draw.text((x, y), line, fill=font_color, font=font)
        current_y += line_heights[i]

    # Save and upload
    output_filename = f"text_image_{uuid.uuid4().hex}.png"
    output_path = os.path.join(temp_dir, output_filename)
    img.save(output_path, format='PNG')

    s3_path = f"image-processing/{output_filename}"
    from app.services.s3.s3 import s3_service
    result_url = await s3_service.upload_file(output_path, s3_path)

    # Clean up
    try:
        os.remove(output_path)
    except Exception as e:
        logger.warning(f"Failed to clean up temporary file: {e}")

    return result_url


async def make_image_wobbly(
    image_url: str,
    wobble_amount: float = 3.0,
    temp_dir: str = "temp"
) -> str:
    """
    Apply a subtle wobble/distortion effect to an image.

    Args:
        image_url: URL or local path of the image to distort
        wobble_amount: Strength of the wobble effect (0.5-10.0, higher = more distortion)
        temp_dir: Temporary directory for processing

    Returns:
        S3 URL of the distorted image
    """
    try:
        # Download or use local image
        if image_url.startswith(('http://', 'https://')):
            image_path = await download_image(image_url, temp_dir=temp_dir)
        else:
            image_path = image_url

        img = Image.open(image_path)

        if img.mode != 'RGB':
            img = img.convert('RGB')

        width, height = img.size
        img_array = np.array(img)

        # Create coordinate grids
        x_coords = np.arange(width)
        y_coords = np.arange(height)
        x_grid, y_grid = np.meshgrid(x_coords, y_coords)

        # Create random wave patterns optimized for text
        freq1_h = np.random.uniform(2, 5)
        freq2_h = np.random.uniform(5, 10)
        phase1_h = np.random.uniform(0, 2 * np.pi)
        phase2_h = np.random.uniform(0, 2 * np.pi)

        wave_x1 = wobble_amount * 0.3 * np.sin(2 * np.pi * y_grid / (height / freq1_h) + phase1_h)
        wave_x2 = wobble_amount * 0.1 * np.sin(2 * np.pi * y_grid / (height / freq2_h) + phase2_h)

        freq1_v = np.random.uniform(2, 6)
        freq2_v = np.random.uniform(6, 12)
        phase1_v = np.random.uniform(0, 2 * np.pi)
        phase2_v = np.random.uniform(0, 2 * np.pi)

        wave_y1 = wobble_amount * 0.3 * np.sin(2 * np.pi * x_grid / (width / freq1_v) + phase1_v)
        wave_y2 = wobble_amount * 0.1 * np.sin(2 * np.pi * x_grid / (width / freq2_v) + phase2_v)

        center_x = width // 2 + np.random.randint(-width//4, width//4)
        center_y = height // 2 + np.random.randint(-height//4, height//4)
        ripple_freq = np.random.uniform(80, 120)
        ripple_phase = np.random.uniform(0, 2 * np.pi)

        distance = np.sqrt((x_grid - center_x)**2 + (y_grid - center_y)**2)
        ripple_x = wobble_amount * 0.15 * np.sin(2 * np.pi * distance / ripple_freq + ripple_phase)
        ripple_y = wobble_amount * 0.15 * np.cos(2 * np.pi * distance / ripple_freq + ripple_phase)

        noise_x = np.random.normal(0, wobble_amount * 0.05, (height, width))
        noise_y = np.random.normal(0, wobble_amount * 0.05, (height, width))

        total_x_offset = wave_x1 + wave_x2 + ripple_x + noise_x
        total_y_offset = wave_y1 + wave_y2 + ripple_y + noise_y

        new_x_coords = x_grid + total_x_offset
        new_y_coords = y_grid + total_y_offset

        try:
            from scipy.ndimage import map_coordinates

            coords = np.array([new_y_coords, new_x_coords])

            distorted_array = np.zeros_like(img_array)

            if wobble_amount <= 1.5:
                interpolation_order = 0
            elif wobble_amount <= 3.0:
                interpolation_order = 1
            else:
                interpolation_order = 3

            for channel in range(img_array.shape[2]):
                distorted_array[:, :, channel] = map_coordinates(
                    img_array[:, :, channel],
                    coords,
                    order=interpolation_order,
                    mode='reflect',
                    prefilter=True if interpolation_order > 1 else False
                )

            result_img = Image.fromarray(distorted_array.astype(np.uint8))

            if wobble_amount > 2.0:
                result_img = result_img.filter(ImageFilter.GaussianBlur(radius=0.3))
                result_img = result_img.filter(ImageFilter.UnsharpMask(radius=0.8, percent=60, threshold=1))
            elif wobble_amount > 1.5:
                result_img = result_img.filter(ImageFilter.UnsharpMask(radius=0.5, percent=40, threshold=0))

        except ImportError:
            # Fallback without scipy
            transformed = img.transform(
                img.size,
                Image.AFFINE,
                (1, 0.02 * wobble_amount/10, 0.02 * wobble_amount/10, 1, 0, 0),
                resample=Image.BILINEAR
            )

            angle = wobble_amount * 0.3 * np.random.uniform(-1, 1)
            result_img = transformed.rotate(angle, resample=Image.BILINEAR, expand=False)

        # Save and upload
        output_filename = f"wobbly_{uuid.uuid4().hex}.jpg"
        output_path = os.path.join(temp_dir, output_filename)
        result_img.save(output_path, format='JPEG', quality=90)

        s3_path = f"image-processing/{output_filename}"
        from app.services.s3.s3 import s3_service
        result_url = await s3_service.upload_file(output_path, s3_path)

        # Clean up
        try:
            os.remove(output_path)
        except Exception as e:
            logger.warning(f"Failed to clean up temporary file: {e}")

        return result_url

    except Exception as e:
        logger.error(f"Failed to make image wobbly: {e}")


def cup_of_coffee_tone(img):
    """Apply a subtle coffee tone effect to the image."""
    sepia = ImageOps.colorize(img.convert("L"), "#704214", "#C0A080")
    return Image.blend(img, sepia, alpha=0.2)


def chromatic_aberration(img, shift=2):
    """Apply chromatic aberration effect by shifting color channels."""
    r, g, b = img.split()
    # Use transform with AFFINE to shift the channels
    r = r.transform(img.size, Image.AFFINE, (1, 0, -shift, 0, 1, 0))
    b = b.transform(img.size, Image.AFFINE, (1, 0, shift, 0, 1, 0))
    return Image.merge("RGB", (r, g, b))


async def make_image_imperfect(
    image_path: str,
    enhance_color: float = None,
    enhance_contrast: float = None,
    noise_strength: int = 15
) -> Image.Image:
    """
    Remove AI-generated artifacts from an image by applying various effects.

    Args:
        image_path: Path to the image file to process
        enhance_color: Strength of color enhancement (0-2, where 0=black&white, 1=no change, 2=max enhancement)
        enhance_contrast: Strength of contrast enhancement (0-2)
        noise_strength: Strength of noise to apply (0-100)

    Returns:
        PIL Image object with imperfections applied
    """
    try:
        img = Image.open(image_path)

        # Apply color and contrast enhancements if specified
        if enhance_color is not None:
            img = ImageEnhance.Color(img).enhance(enhance_color)
        if enhance_contrast is not None:
            img = ImageEnhance.Contrast(img).enhance(enhance_contrast)

        # Apply sharpening and slight blur to reduce AI artifacts
        img = img.filter(ImageFilter.SHARPEN)
        img = img.filter(ImageFilter.GaussianBlur(radius=0.5))

        # Convert to RGB if necessary and add noise
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img_array = np.array(img)
        h, w, c = img_array.shape

        # Add grayscale noise to all channels
        grayscale_noise = np.random.randint(-noise_strength, noise_strength + 1, (h, w), dtype='int16')
        noise = np.stack([grayscale_noise] * c, axis=2)
        noisy_array = img_array.astype('int16') + noise
        noisy_array = np.clip(noisy_array, 0, 255).astype('uint8')
        img = Image.fromarray(noisy_array)

        # Apply coffee tone and chromatic aberration for additional imperfection
        img = cup_of_coffee_tone(img)
        img = chromatic_aberration(img, shift=1)

        return img

    except Exception as e:
        logger.error(f"Failed to make image imperfect from {image_path}: {e}")
        raise ValueError("Failed to process image imperfections") from e


async def resize_image_cover(
    image_path: str,
    target_width: int,
    target_height: int,
    output_path: str = None
) -> Image.Image:
    """
    Resize an image to fill the specified dimensions while maintaining aspect ratio.
    The image is scaled to cover the entire target area and cropped to fit.

    Args:
        image_path: Path to the input image file
        target_width: Target width
        target_height: Target height
        output_path: Optional output path to save the resized image

    Returns:
        Resized and cropped PIL Image object
    """
    image = Image.open(image_path)

    # Calculate the scaling factor to cover the entire target area
    width_ratio = target_width / image.width
    height_ratio = target_height / image.height
    scale_factor = max(width_ratio, height_ratio)  # Use max to ensure coverage

    # Scale the image
    new_width = int(image.width * scale_factor)
    new_height = int(image.height * scale_factor)
    scaled_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Calculate crop box to center the image
    left = (new_width - target_width) // 2
    top = (new_height - target_height) // 2
    right = left + target_width
    bottom = top + target_height

    # Crop the image to the target dimensions
    cropped_image = scaled_image.crop((left, top, right, bottom))

    # Convert to RGB if the image has transparency (RGBA mode)
    if cropped_image.mode == 'RGBA':
        # Create a white background and paste the image on it
        rgb_image = Image.new('RGB', cropped_image.size, (255, 255, 255))
        rgb_image.paste(cropped_image, mask=cropped_image.split()[-1])  # Use alpha channel as mask
        cropped_image = rgb_image

    # Save to output path if provided
    if output_path:
        cropped_image.save(output_path, format='JPEG', quality=95)

    return cropped_image
