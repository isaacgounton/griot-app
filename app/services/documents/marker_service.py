"""
Marker Document Processing Service

Provides high-quality document conversion using the Marker library.
Supports PDF, DOCX, PPTX, XLSX, images, HTML, EPUB, and more.
"""

import os
import json
import asyncio
import tempfile
from typing import Dict, Any, Optional
from pathlib import Path

from app.models import JobType
import logging

logger = logging.getLogger(__name__)

class MarkerService:
    def __init__(self):
        # Configure for CPU-only operation
        os.environ["TORCH_DEVICE"] = "cpu"
        
        # Configure LLM API keys from environment
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL")
        
        # Use GEMINI_API_KEY for Gemini (Google AI)
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.gemini_model = os.getenv("GEMINI_MODEL", "google/gemini-2.5-flash")
        
    async def convert_document(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert document using Marker with CPU-only processing.
        
        Args:
            params: Dictionary containing:
                - file_path: Path to local file to process
                - output_format: 'markdown', 'json', 'html', or 'chunks' (default: markdown)
                - force_ocr: Force OCR on all text (default: False)
                - preserve_images: Extract and save images (default: True)
                - use_llm: Use LLM for enhanced accuracy (default: False)
                - paginate_output: Add page breaks (default: False)
                - original_filename: Original filename for metadata
        
        Returns:
            Dictionary with conversion results and metadata
        """
        try:
            # Import marker here to avoid startup issues
            from marker.converters.pdf import PdfConverter
            from marker.models import create_model_dict
            from marker.output import text_from_rendered
            from marker.config.parser import ConfigParser
            
            file_path = params.get("file_path")
            output_format = params.get("output_format", "markdown")
            force_ocr = params.get("force_ocr", False)
            preserve_images = params.get("preserve_images", True)
            use_llm = params.get("use_llm", False)
            paginate_output = params.get("paginate_output", False)
            original_filename = params.get("original_filename", Path(file_path).name)
            
            if not file_path or not os.path.exists(file_path):
                raise ValueError("File path is required and must exist")
            
            # Configure Marker for CPU-only operation
            config = {
                "output_format": output_format,
                "force_ocr": force_ocr,
                "paginate_output": paginate_output,
                "disable_image_extraction": not preserve_images,
                "use_llm": use_llm,
                "torch_device": "cpu",
                "workers": 1,  # Single worker for CPU
            }
            
            # Configure LLM service if requested
            llm_service = params.get("llm_service", "openai")
            llm_service_instance = None
            if use_llm and llm_service:
                llm_service_instance = self._configure_llm_service(llm_service)
                if llm_service_instance:
                    logger.info(f"Using LLM service: {llm_service}")
                else:
                    logger.warning(f"Failed to configure LLM service: {llm_service}, proceeding without LLM")
            
            logger.info(f"Processing document: {original_filename} with format: {output_format}")
            
            # Create model dictionary for CPU inference
            model_dict = create_model_dict()
            
            # Configure parser
            config_parser = ConfigParser(config)
            
            # Create converter with CPU configuration
            converter = PdfConverter(
                config=config_parser.generate_config_dict(),
                artifact_dict=model_dict,
                processor_list=config_parser.get_processors(),
                renderer=config_parser.get_renderer(),
                llm_service=llm_service_instance
            )
            
            # Process the document with timeout protection
            try:
                # Set a generous timeout for document processing (30 minutes)
                # Large documents with many text blocks can take significant time
                rendered = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, 
                        converter, 
                        file_path
                    ),
                    timeout=1800  # 30 minutes
                )
            except asyncio.TimeoutError:
                raise TimeoutError("Document processing timed out after 30 minutes")
            
            # Extract text and images based on output format
            if output_format == "markdown":
                text, metadata, images = text_from_rendered(rendered)
                content = text
            elif output_format == "json":
                content = rendered.model_dump_json(indent=2)
                metadata = rendered.metadata if hasattr(rendered, 'metadata') else {}
                images = rendered.images if hasattr(rendered, 'images') else {}
            elif output_format == "html":
                # Convert to HTML format
                from marker.output import html_from_rendered
                html, metadata, images = html_from_rendered(rendered)
                content = html
            else:  # chunks
                # Convert to chunks format
                content = rendered.model_dump_json(indent=2)
                metadata = rendered.metadata if hasattr(rendered, 'metadata') else {}
                images = rendered.images if hasattr(rendered, 'images') else {}
            
            # Calculate statistics
            word_count = len(content.split()) if isinstance(content, str) else 0
            character_count = len(content) if isinstance(content, str) else 0
            
            # Save images to S3 if present
            image_urls = {}
            if images and preserve_images:
                for image_name, image_data in images.items():
                    try:
                        # Save image to temporary file
                        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                            temp_file.write(image_data)
                            temp_path = temp_file.name
                        
                        # Upload to S3
                        from app.services.s3.s3 import s3_service
                        s3_key = f"marker_images/{image_name}"
                        s3_url = await s3_service.upload_file(temp_path, s3_key)
                        image_urls[image_name] = s3_url
                        
                        # Clean up temp file
                        os.unlink(temp_path)
                        
                    except Exception as e:
                        logger.warning(f"Failed to save image {image_name}: {str(e)}")
            
            # Save main content to S3
            output_extension = {
                "markdown": ".md",
                "json": ".json", 
                "html": ".html",
                "chunks": ".json"
            }.get(output_format, ".txt")
            
            filename_base = Path(original_filename).stem
            output_filename = f"{filename_base}_marker{output_extension}"
            
            with tempfile.NamedTemporaryFile(mode='w', suffix=output_extension, delete=False) as temp_file:
                temp_file.write(content)
                temp_path = temp_file.name
            
            # Upload to S3
            from app.services.s3.s3 import s3_service
            s3_key = f"marker_documents/{output_filename}"
            content_url = await s3_service.upload_file(temp_path, s3_key)
            
            # Clean up temp file
            os.unlink(temp_path)
            
            # Prepare result
            result = {
                "content": content,
                "content_url": content_url,
                "original_filename": original_filename,
                "output_filename": output_filename,
                "output_format": output_format,
                "word_count": word_count,
                "character_count": character_count,
                "image_count": len(images) if images else 0,
                "image_urls": image_urls,
                "metadata": metadata if isinstance(metadata, dict) else {},
                "processing_settings": {
                    "force_ocr": force_ocr,
                    "preserve_images": preserve_images,
                    "use_llm": use_llm,
                    "paginate_output": paginate_output,
                    "torch_device": "cpu"
                }
            }
            
            logger.info(f"Successfully processed {original_filename}: {word_count} words, {len(images) if images else 0} images")
            return result
            
        except Exception as e:
            logger.error(f"Marker conversion failed: {str(e)}")
            raise Exception(f"Document conversion failed: {str(e)}")
    
    async def get_supported_formats(self) -> Dict[str, Any]:
        """
        Get list of supported input and output formats.
        
        Returns:
            Dictionary with supported formats and capabilities
        """
        return {
            "input_formats": [
                "pdf", "docx", "doc", "pptx", "ppt", "xlsx", "xls",
                "png", "jpg", "jpeg", "gif", "bmp", "tiff",
                "html", "htm", "epub", "txt"
            ],
            "output_formats": [
                "markdown", "json", "html", "chunks"
            ],
            "features": [
                "table_formatting",
                "equation_processing", 
                "image_extraction",
                "header_footer_removal",
                "code_block_formatting",
                "reference_links",
                "multi_language_support",
                "cpu_processing",
                "llm_enhancement"
            ],
            "llm_services": [
                "openai", "gemini"
            ],
            "available_llm_services": self._get_available_llm_services()
        }
    
    def _get_available_llm_services(self) -> Dict[str, Dict[str, Any]]:
        """Get available LLM services based on configured API keys."""
        services = {}
        
        if self.openai_api_key:
            services["openai"] = {
                "name": "OpenAI",
                "model": self.openai_model,
                "base_url": self.openai_base_url,
                "available": True,
                "features": ["table_merging", "inline_math", "form_extraction", "layout_analysis"]
            }
        
        if self.gemini_api_key:
            services["gemini"] = {
                "name": "Google Gemini",
                "model": self.gemini_model,
                "available": True,
                "features": ["table_merging", "inline_math", "form_extraction", "content_correction"]
            }
        
        return services
    
    def _configure_llm_service(self, llm_service: str):
        """Configure LLM service for Marker."""
        try:
            if llm_service == "openai" and self.openai_api_key:
                from marker.llm.openai_api import OpenAIApi
                
                # Configure OpenAI client
                config = {
                    "api_key": self.openai_api_key,
                    "model": self.openai_model,
                }
                
                if self.openai_base_url:
                    config["base_url"] = self.openai_base_url
                
                return OpenAIApi(**config)
                
            elif llm_service == "gemini" and self.gemini_api_key:
                from marker.llm.google_genai import GoogleGenAI
                
                # Configure Gemini client
                config = {
                    "api_key": self.gemini_api_key,
                    "model": self.gemini_model,
                }
                
                return GoogleGenAI(**config)
                
            else:
                logger.warning(f"LLM service '{llm_service}' not available or API key missing")
                return None
                
        except ImportError as e:
            logger.warning(f"Failed to import LLM service '{llm_service}': {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Failed to configure LLM service '{llm_service}': {str(e)}")
            return None

# Create service instance
marker_service = MarkerService()