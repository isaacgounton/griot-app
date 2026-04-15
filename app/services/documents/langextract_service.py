"""
Langextract service for AI-powered structured data extraction from text.

This service uses Google's Langextract library to extract structured information
from unstructured text using large language models (LLMs) with source grounding.
Supports both Google Gemini and OpenAI-compatible providers (including OpenRouter).
"""
import os
import logging
from typing import Any
from datetime import datetime, timezone
import json

# from app.services.s3.s3 import s3_service  # Temporarily disabled to avoid circular imports

logger = logging.getLogger(__name__)


class LangextractService:
    """Service for AI-powered structured data extraction using Google Langextract."""
    
    def __init__(self):
        """Initialize the Langextract service."""
        self._available = None
        self._langextract = None
        
    def is_available(self) -> bool:
        """Check if Langextract service is available."""
        if self._available is None:
            try:
                import langextract as lx
                self._langextract = lx
                self._available = True
                logger.info("Langextract service is available")
            except ImportError as e:
                logger.warning(f"Langextract not available: {e}")
                self._available = False
                self._langextract = None
        return self._available

    def get_supported_models(self) -> dict[str, Any]:
        """Get information about supported AI models and capabilities."""
        return {
            "available": self.is_available(),
            "supported_models": {
                "gemini": {
                    "provider": "Google Gemini",
                    "description": "Google's multimodal AI model (primary)",
                    "model_id": "gemini-2.0-flash-exp",
                    "supported_features": [
                        "Named entity extraction",
                        "Relationship extraction", 
                        "Custom schema definition",
                        "Source grounding",
                        "Multi-language support"
                    ],
                    "requires": "GEMINI_API_KEY environment variable"
                },
                "openai": {
                    "provider": "OpenAI API / OpenRouter",
                    "description": "OpenAI models via official API or OpenRouter (fallback)",
                    "configured_model": os.getenv('OPENAI_VISION_MODEL', 'gpt-4o-mini'),
                    "effective_model": self._get_effective_openai_model(),
                    "direct_openai_models": ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'],
                    "openrouter_models": "All OpenRouter-supported models (auto-detected by sk-or- key)",
                    "supported_features": [
                        "Named entity extraction",
                        "Relationship extraction",
                        "Custom schema definition", 
                        "Source grounding",
                        "Enhanced prompt handling",
                        "OpenRouter compatibility"
                    ],
                    "requires": "OPENAI_API_KEY environment variable (sk-... or sk-or-...)",
                    "configuration": "Set OPENAI_VISION_MODEL to customize model. OpenRouter keys support any model."
                }
            },
            "extraction_types": {
                "entities": "Named entities like people, organizations, locations",
                "relationships": "Relationships between entities",
                "attributes": "Properties and attributes of entities",
                "custom_schema": "User-defined extraction schemas"
            },
            "input_formats": [
                "Plain text",
                "Document URLs (PDF, Word, HTML)",
                "File uploads (PDF, DOCX, TXT, HTML)"
            ],
            "features": [
                "Source grounding (exact text location mapping)",
                "Interactive HTML visualization", 
                "JSON structured output",
                "Confidence scoring",
                "Parallel processing support"
            ]
        }

    async def extract_structured_data(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        Extract structured data from text using Langextract.
        
        Args:
            params: Dictionary containing:
                - input_text: Text content to extract from (optional)
                - file_url: URL to document to extract from (optional)  
                - file_content: Binary file content (optional)
                - input_filename: Original filename for context
                - extraction_schema: JSON schema defining what to extract
                - extraction_prompt: Custom prompt for extraction
                - use_custom_prompt: Whether to use custom prompt vs schema
                - model: AI model to use ('gemini' or 'openai')
                
        Returns:
            Dictionary containing extracted data with source grounding
        """
        if not self.is_available():
            raise ValueError("Langextract service is not available")
            
        start_time = datetime.now()
        
        try:
            # Prepare input text
            input_text = await self._prepare_input_text(params)
            
            if not input_text or len(input_text.strip()) < 10:
                raise ValueError("Input text is too short or empty for meaningful extraction")
            
            # Get the appropriate model ID
            model_id = await self._get_model_id(params.get('model', 'gemini'))
            
            # Prepare extraction configuration
            extraction_config = await self._prepare_extraction_config(params)
            
            # Perform extraction using langextract with fallback support
            logger.info(f"Starting Langextract extraction with model: {model_id}")
            
            # Use langextract API
            lx = self._langextract
            if lx is None:
                raise ValueError("Langextract is not available - service not properly initialized")
            
            result, actual_model_used = await self._perform_extraction_with_fallback(
                lx, input_text, extraction_config, params, model_id
            )
            
            # Process and structure results
            processed_results = await self._process_extraction_results(result, input_text)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Prepare enhanced final result
            final_result = {
                "extracted_data": processed_results,
                "total_extractions": sum(len(entities) for entities in processed_results.values()),
                "processing_time": processing_time,
                "model_used": actual_model_used,
                "input_text_length": len(input_text),
                "input_filename": params.get('input_filename', 'unknown'),
                "extraction_type": "custom_prompt" if params.get('use_custom_prompt') else "schema_based",
                "source_grounding_enabled": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "extraction_config": {
                    "entity_types": list(processed_results.keys()),
                    "has_attributes": any(
                        any("attributes" in entity for entity in entities) 
                        for entities in processed_results.values()
                    ),
                    "extraction_passes": 2,  # Enhanced configuration
                    "max_workers": 10,
                    "temperature": 0.3
                },
                "quality_metrics": {
                    "entities_with_attributes": sum(
                        sum(1 for entity in entities if "attributes" in entity)
                        for entities in processed_results.values()
                    ),
                    "average_confidence": sum(
                        sum(entity.get("confidence_score", 0.0) for entity in entities)
                        for entities in processed_results.values()
                    ) / max(1, sum(len(entities) for entities in processed_results.values())),
                    "unique_entity_types": len(processed_results),
                    "processing_speed_chars_per_sec": len(input_text) / max(0.1, processing_time)
                }
            }
            
            # Store results in S3 for later retrieval
            # await self._store_results_in_s3(final_result, input_text)  # Temporarily disabled
            
            logger.info(f"Langextract extraction completed in {processing_time:.2f}s with {final_result['total_extractions']} extractions")
            
            return final_result
            
        except Exception as e:
            logger.error(f"Langextract extraction failed: {str(e)}")
            raise ValueError(f"Data extraction failed: {str(e)}")
    
    async def _perform_extraction_with_fallback(self, lx, input_text: str, 
                                               extraction_config: dict[str, Any], 
                                               params: dict[str, Any], 
                                               model_id: str):
        """Perform extraction with automatic fallback to OpenAI on Gemini errors."""
        try:
            result = self._perform_single_extraction(lx, input_text, extraction_config, params, model_id)
            return result, model_id
        except Exception as e:
            error_str = str(e).lower()
            # Check for Gemini quota/rate limit errors
            if (model_id.startswith('gemini') and 
                ('quota' in error_str or 'rate' in error_str or '429' in error_str or 
                 'resource_exhausted' in error_str or 'exceeded your current quota' in error_str)):
                
                logger.warning(f"Gemini API quota/rate limit exceeded, falling back to OpenAI: {str(e)[:200]}...")
                
                # Check if OpenAI is available as fallback
                openai_key = os.getenv('OPENAI_API_KEY')
                if openai_key:
                    try:
                        # Use configurable OpenAI model from environment variable
                        configured_model = os.getenv('OPENAI_VISION_MODEL', 'gpt-4o-mini')
                        
                        # Check if using OpenRouter (more flexible with model names)
                        is_openrouter = openai_key.startswith('sk-or-')
                        
                        if is_openrouter:
                            # OpenRouter supports many models, use configured model directly
                            openai_model_id = configured_model
                            fallback_note = f"{openai_model_id} via OpenRouter (fallback from {model_id})"
                            logger.info(f"Using OpenRouter with model: {configured_model}")
                        else:
                            # Direct OpenAI - check against supported models
                            supported_models = ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo']
                            if configured_model not in supported_models:
                                logger.warning(f"Configured model '{configured_model}' not supported by direct OpenAI. "
                                             f"Direct OpenAI only supports: {', '.join(supported_models)}. Using gpt-4o-mini.")
                                openai_model_id = 'gpt-4o-mini'
                                fallback_note = f"gpt-4o-mini (configured: {configured_model}, fallback from {model_id})"
                            else:
                                openai_model_id = configured_model
                                fallback_note = f"{openai_model_id} (fallback from {model_id})"
                        
                        logger.info(f"Retrying extraction with OpenAI model: {openai_model_id}")
                        result = self._perform_single_extraction(lx, input_text, extraction_config, params, openai_model_id)
                        return result, fallback_note
                    except Exception as openai_error:
                        logger.error(f"OpenAI fallback also failed: {str(openai_error)}")
                        raise ValueError(f"Both Gemini and OpenAI extraction failed. Gemini: {str(e)[:200]}... OpenAI: {str(openai_error)[:200]}...") from openai_error
                else:
                    logger.error("No OpenAI API key available for fallback")
                    raise ValueError(f"Gemini quota exceeded and no OpenAI fallback available: {str(e)}") from e
            else:
                # Re-raise original error if it's not a quota/rate limit issue
                raise
    
    def _perform_single_extraction(self, lx, input_text: str, extraction_config: dict[str, Any], 
                                  params: dict[str, Any], model_id: str):
        """Perform a single extraction attempt with the specified model."""
        # Get the appropriate API key for this model
        api_key = self._get_api_key_for_model(model_id)
        
        # Check if using OpenRouter (detected by key prefix)
        is_openrouter = api_key.startswith('sk-or-') if api_key else False
        
        # Configure extraction parameters based on model type and provider
        extract_params: dict[str, Any] = {
            'text_or_documents': input_text,
            'model_id': model_id,
            'api_key': api_key,
            'extraction_passes': 2,  # Multiple passes for better recall
            'max_workers': 10,       # Parallel processing 
            'max_char_buffer': 1000, # Smaller contexts for better accuracy
            'temperature': 0.3       # More consistent results
        }
        
        # Add model-specific parameters
        if model_id.startswith('gpt') or is_openrouter:
            # Use OpenAI language model type for OpenAI-compatible models
            extract_params['language_model_type'] = lx.inference.OpenAILanguageModel
            extract_params['fence_output'] = True
            extract_params['use_schema_constraints'] = False
            
            # Add OpenRouter-specific configuration if detected
            if is_openrouter:
                openai_base_url = os.getenv('OPENAI_BASE_URL')
                if openai_base_url:
                    # Pass custom base URL via language_model_params
                    extract_params['language_model_params'] = {
                        'base_url': openai_base_url
                    }
                    logger.info(f"Using OpenRouter base URL: {openai_base_url} with model: {model_id}")
        else:
            # Use Gemini language model type for Gemini models (default)
            extract_params['language_model_type'] = lx.inference.GeminiLanguageModel
        
        if params.get('use_custom_prompt', False):
            # Use custom prompt extraction
            prompt = extraction_config['prompt']
            examples = self._create_example_data(prompt)
            
            extract_params['prompt_description'] = prompt
            extract_params['examples'] = examples
            
            return lx.extract(**extract_params)
        else:
            # Use schema-based extraction with comprehensive prompt
            schema = extraction_config['schema']
            entities = schema.get('entities', [])
            relationships = schema.get('relationships', [])
            
            # Create a comprehensive prompt description
            prompt_parts = [
                "Extract structured information from the given text with high accuracy and meaningful context.",
                "",
                "IMPORTANT: Use exact text from the input for extraction_text. Do not paraphrase or modify.",
                "Extract entities in order of appearance with no overlapping text spans.",
                "Provide meaningful attributes for every entity to add context and depth.",
                ""
            ]
            
            if entities:
                prompt_parts.extend([
                    f"Extract the following entity types: {', '.join(entities)}",
                    ""
                ])
                
                # Add specific guidance for common entity types
                entity_guidance = {
                    'person': "For people, include titles, roles, and context attributes",
                    'organization': "For organizations, specify type (company/startup/university) and industry", 
                    'location': "For locations, specify type (city/state/country) and context",
                    'financial_metric': "For financial data, include amount, currency, and context",
                    'job_title': "For job titles, link to associated person and organization",
                    'funding_round': "For funding rounds, include stage, amount, and participants"
                }
                
                guidance_items = [f"- {entity_guidance[entity]}" for entity in entities if entity in entity_guidance]
                if guidance_items:
                    prompt_parts.extend([
                        "Entity-specific guidelines:",
                        *guidance_items,
                        ""
                    ])
            
            if relationships:
                prompt_parts.extend([
                    f"Identify relationships: {', '.join(relationships)}",
                    "For relationships, specify the connection type and involved entities.",
                    ""
                ])
            
            prompt_parts.append("Focus on accuracy, completeness, and providing rich contextual attributes.")
            
            prompt = "\n".join(prompt_parts)
            examples = self._create_example_data_for_schema(schema)
            
            extract_params['prompt_description'] = prompt
            extract_params['examples'] = examples
            
            return lx.extract(**extract_params)
    
    def _get_effective_openai_model(self) -> str:
        """Get the effective OpenAI model that will actually be used."""
        configured_model = os.getenv('OPENAI_VISION_MODEL', 'gpt-4o-mini')
        supported_models = ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo']
        
        if configured_model not in supported_models:
            return f"gpt-4o-mini (mapped from {configured_model})"
        return configured_model
    
    def _get_api_key_for_model(self, model_id: str) -> str:
        """Get the appropriate API key for a given model ID."""
        if model_id.startswith('gemini'):
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                raise ValueError(f"GEMINI_API_KEY is required for model {model_id}")
            return api_key
        elif model_id.startswith('gpt') or 'openai' in model_id.lower():
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError(f"OPENAI_API_KEY is required for model {model_id}")
            return api_key
        else:
            # Try to determine from model name or fall back to Gemini
            api_key = os.getenv('GEMINI_API_KEY') or os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError(f"No API key available for model {model_id}")
            return api_key

    async def _prepare_input_text(self, params: dict[str, Any]) -> str:
        """Prepare input text from various sources."""
        # Direct text input
        if params.get('input_text'):
            return params['input_text']
            
        # File content (binary)
        if params.get('file_content'):
            # For now, assume text files. In production, you'd want document parsing
            try:
                return params['file_content'].decode('utf-8')
            except UnicodeDecodeError:
                # Try other encodings or use document parsing
                return params['file_content'].decode('utf-8', errors='ignore')
                
        # URL-based content
        if params.get('file_url'):
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(params['file_url']) as response:
                    response.raise_for_status()
                    return await response.text()
            
        raise ValueError("No input text, file content, or URL provided")

    async def _get_model_id(self, model: str = 'gemini') -> str:
        """Get the appropriate model ID for langextract."""
        # Handle fallback from gemini to openai when no GEMINI_API_KEY
        if model == 'gemini':
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                logger.warning("GEMINI_API_KEY not found, falling back to OpenAI")
                model = 'openai'
        
        # Now check the final model choice
        if model == 'openai':
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("Neither GEMINI_API_KEY nor OPENAI_API_KEY is configured")
                
            # Use configurable OpenAI model from environment variable
            openai_model = os.getenv('OPENAI_VISION_MODEL', 'gpt-4o-mini')
            
            # Check if using OpenRouter (more flexible with model support)
            is_openrouter = api_key.startswith('sk-or-')
            
            if is_openrouter:
                # OpenRouter supports many models, use configured model directly
                logger.info(f"Using OpenRouter with model: {openai_model}")
                return openai_model
            else:
                # Direct OpenAI - check against supported models
                supported_models = ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo']
                if openai_model not in supported_models:
                    logger.warning(f"Model '{openai_model}' not supported by direct OpenAI. Using gpt-4o-mini as fallback.")
                    return 'gpt-4o-mini'
                return openai_model
        elif model == 'gemini':
            # This means we have a Gemini API key (checked above)
            return "gemini-2.0-flash-exp"  # Use the latest Gemini model
        else:
            raise ValueError(f"Unknown model type: {model}. Use 'gemini' or 'openai'.")

    async def _prepare_extraction_config(self, params: dict[str, Any]) -> dict[str, Any]:
        """Prepare extraction configuration from parameters."""
        config = {}
        
        if params.get('use_custom_prompt', False):
            config['prompt'] = params.get('extraction_prompt', 
                'Extract all important entities, relationships, and attributes from the text.')
        else:
            # Parse schema JSON
            schema_str = params.get('extraction_schema', '{}')
            try:
                config['schema'] = json.loads(schema_str)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON schema provided, using default")
                config['schema'] = {
                    "entities": ["person", "organization", "location"],
                    "relationships": ["works_for", "located_in"]
                }
                
        return config

    def _create_example_data_for_schema(self, schema: dict[str, Any]) -> list[Any]:
        """Create rich example data based on extraction schema with meaningful attributes."""
        lx = self._langextract
        if lx is None:
            raise ValueError("Langextract is not available - service not properly initialized")
            
        examples = []
        entities = schema.get('entities', [])
        
        if not entities:
            return []
        
        # Create comprehensive business context example
        if 'person' in entities and 'organization' in entities:
            example_text = "Dr. Maria Rodriguez, Chief Technology Officer at InnovateAI Corp, announced the company's breakthrough in artificial intelligence research from their headquarters in Austin, Texas."
            extractions = []
            
            # Person with detailed attributes
            extractions.append(lx.data.Extraction(
                extraction_class="person",
                extraction_text="Dr. Maria Rodriguez",
                attributes={
                    "title": "Dr.", 
                    "role": "Chief Technology Officer",
                    "context": "business_announcement",
                    "full_name": "Maria Rodriguez"
                }
            ))
            
            # Job title if requested
            if 'job_title' in entities:
                extractions.append(lx.data.Extraction(
                    extraction_class="job_title",
                    extraction_text="Chief Technology Officer",
                    attributes={
                        "person": "Maria Rodriguez",
                        "organization": "InnovateAI Corp",
                        "level": "executive"
                    }
                ))
            
            # Organization with rich context
            extractions.append(lx.data.Extraction(
                extraction_class="organization",
                extraction_text="InnovateAI Corp",
                attributes={
                    "industry": "technology",
                    "focus": "artificial intelligence",
                    "type": "corporation"
                }
            ))
            
            # Location if requested
            if 'location' in entities:
                extractions.append(lx.data.Extraction(
                    extraction_class="location",
                    extraction_text="Austin, Texas",
                    attributes={
                        "type": "city_state",
                        "context": "headquarters"
                    }
                ))
            
            examples.append(lx.data.ExampleData(
                text=example_text,
                extractions=extractions
            ))
        
        # Financial/funding context example
        if 'financial_metric' in entities or 'funding_round' in entities:
            example_text = "TechStart Inc. successfully raised $75 million in Series B funding led by venture capital firm Growth Partners, bringing total funding to $120 million."
            extractions = []
            
            if 'organization' in entities:
                extractions.append(lx.data.Extraction(
                    extraction_class="organization",
                    extraction_text="TechStart Inc.",
                    attributes={"type": "startup", "stage": "Series B", "status": "funded"}
                ))
                
                extractions.append(lx.data.Extraction(
                    extraction_class="organization", 
                    extraction_text="Growth Partners",
                    attributes={"type": "venture_capital", "role": "lead_investor"}
                ))
            
            if 'financial_metric' in entities:
                extractions.append(lx.data.Extraction(
                    extraction_class="financial_metric",
                    extraction_text="$75 million",
                    attributes={
                        "amount": "75000000",
                        "currency": "USD",
                        "type": "funding_round"
                    }
                ))
                
                extractions.append(lx.data.Extraction(
                    extraction_class="financial_metric",
                    extraction_text="$120 million",
                    attributes={
                        "amount": "120000000", 
                        "currency": "USD",
                        "type": "total_funding"
                    }
                ))
            
            if 'funding_round' in entities:
                extractions.append(lx.data.Extraction(
                    extraction_class="funding_round",
                    extraction_text="Series B",
                    attributes={
                        "stage": "growth",
                        "amount": "$75 million",
                        "company": "TechStart Inc."
                    }
                ))
            
            examples.append(lx.data.ExampleData(
                text=example_text,
                extractions=extractions
            ))
        
        # Generic fallback for other entity types
        if not examples and entities:
            entity_type = entities[0]
            example_text = "This is a comprehensive example text designed to demonstrate high-quality entity extraction with contextual understanding."
            extractions = [
                lx.data.Extraction(
                    extraction_class=entity_type,
                    extraction_text="comprehensive example",
                    attributes={
                        "context": "demonstration",
                        "quality": "high"
                    }
                )
            ]
            examples.append(lx.data.ExampleData(
                text=example_text,
                extractions=extractions
            ))
            
        return examples

    def _create_example_data(self, prompt: str) -> list[Any]:
        """Create rich example data based on custom prompt with meaningful attributes."""
        lx = self._langextract
        if lx is None:
            raise ValueError("Langextract is not available - service not properly initialized")
        
        # Create contextual examples based on prompt content
        prompt_lower = prompt.lower()
        
        # Business/corporate context
        if any(word in prompt_lower for word in ['company', 'business', 'corporate', 'organization', 'ceo', 'executive']):
            example_text = "Sarah Chen, CEO of DataFlow Technologies, announced the acquisition of startup CloudAnalytics for $45 million at the company's Silicon Valley headquarters."
            extractions = [
                lx.data.Extraction(
                    extraction_class="person",
                    extraction_text="Sarah Chen",
                    attributes={"role": "CEO", "context": "business_announcement"}
                ),
                lx.data.Extraction(
                    extraction_class="organization",
                    extraction_text="DataFlow Technologies", 
                    attributes={"type": "acquirer", "industry": "technology"}
                ),
                lx.data.Extraction(
                    extraction_class="organization",
                    extraction_text="CloudAnalytics",
                    attributes={"type": "startup", "status": "acquired"}
                ),
                lx.data.Extraction(
                    extraction_class="financial_metric",
                    extraction_text="$45 million",
                    attributes={"amount": "45000000", "currency": "USD", "type": "acquisition"}
                ),
                lx.data.Extraction(
                    extraction_class="location", 
                    extraction_text="Silicon Valley",
                    attributes={"type": "region", "context": "headquarters"}
                )
            ]
        # Research/academic context  
        elif any(word in prompt_lower for word in ['research', 'study', 'academic', 'university', 'professor']):
            example_text = "Professor Emily Watson from Stanford University published groundbreaking research on machine learning algorithms in Nature journal, collaborating with researchers from MIT."
            extractions = [
                lx.data.Extraction(
                    extraction_class="person",
                    extraction_text="Professor Emily Watson",
                    attributes={"title": "Professor", "field": "machine learning"}
                ),
                lx.data.Extraction(
                    extraction_class="organization",
                    extraction_text="Stanford University",
                    attributes={"type": "university", "role": "primary_affiliation"}
                ),
                lx.data.Extraction(
                    extraction_class="organization",
                    extraction_text="Nature journal",
                    attributes={"type": "publication", "prestige": "high"}
                ),
                lx.data.Extraction(
                    extraction_class="organization",
                    extraction_text="MIT",
                    attributes={"type": "university", "role": "collaborator"}
                )
            ]
        # Generic high-quality example
        else:
            example_text = "Dr. Alex Rivera, the innovative founder of GreenTech Solutions, presented the company's revolutionary solar technology at the International Energy Conference in Berlin, attracting $30 million in new investments."
            extractions = [
                lx.data.Extraction(
                    extraction_class="person",
                    extraction_text="Dr. Alex Rivera",
                    attributes={"title": "Dr.", "role": "founder", "expertise": "clean_energy"}
                ),
                lx.data.Extraction(
                    extraction_class="organization",
                    extraction_text="GreenTech Solutions",
                    attributes={"industry": "clean_energy", "stage": "growth"}
                ),
                lx.data.Extraction(
                    extraction_class="event",
                    extraction_text="International Energy Conference",
                    attributes={"type": "conference", "focus": "energy"}
                ),
                lx.data.Extraction(
                    extraction_class="location",
                    extraction_text="Berlin",
                    attributes={"type": "city", "context": "conference_venue"}
                ),
                lx.data.Extraction(
                    extraction_class="financial_metric",
                    extraction_text="$30 million",
                    attributes={"amount": "30000000", "currency": "USD", "type": "investment"}
                )
            ]
        
        return [lx.data.ExampleData(
            text=example_text,
            extractions=extractions
        )]

    async def _process_extraction_results(self, results: Any, original_text: str) -> dict[str, list[dict[str, Any]]]:
        """Process and structure extraction results with source grounding."""
        processed = {}
        
        try:
            # Langextract returns AnnotatedDocument with extractions
            if hasattr(results, 'extractions'):
                # Group extractions by class
                extraction_groups = {}
                
                for extraction in results.extractions:
                    extraction_class = getattr(extraction, 'extraction_class', 'unknown')
                    extraction_text = getattr(extraction, 'extraction_text', str(extraction))
                    
                    if extraction_class not in extraction_groups:
                        extraction_groups[extraction_class] = []
                    
                    # Create entity with enhanced source grounding and attributes
                    entity = {
                        "text": extraction_text,
                        "value": extraction_text,  # Keep for backwards compatibility
                        "sources": [],
                        "confidence_score": getattr(extraction, 'score', 0.0)
                    }
                    
                    # Add rich attributes if available
                    attributes = getattr(extraction, 'attributes', {})
                    if attributes:
                        entity["attributes"] = attributes
                        
                        # Extract key context information to top level for easier access
                        if "context" in attributes:
                            entity["context"] = attributes["context"]
                        if "type" in attributes:
                            entity["type"] = attributes["type"]
                        if "role" in attributes:
                            entity["role"] = attributes["role"]
                    
                    # Add source grounding from char_interval
                    char_interval = getattr(extraction, 'char_interval', None)
                    if char_interval and hasattr(char_interval, 'start_pos') and hasattr(char_interval, 'end_pos'):
                        start = char_interval.start_pos or 0
                        end = char_interval.end_pos or len(extraction_text)
                        
                        # Ensure bounds are within text
                        start = max(0, min(start, len(original_text)))
                        end = max(start, min(end, len(original_text)))
                        
                        entity["sources"].append({
                            "start": start,
                            "end": end,
                            "text": original_text[start:end] if start < end else extraction_text
                        })
                    else:
                        # Fallback source grounding - try to find the text in original
                        try:
                            index = original_text.lower().find(extraction_text.lower())
                            if index >= 0:
                                entity["sources"].append({
                                    "start": index,
                                    "end": index + len(extraction_text),
                                    "text": original_text[index:index + len(extraction_text)]
                                })
                            else:
                                entity["sources"].append({
                                    "start": 0,
                                    "end": len(extraction_text),
                                    "text": extraction_text
                                })
                        except Exception:
                            entity["sources"].append({
                                "start": 0,
                                "end": len(extraction_text),
                                "text": extraction_text
                            })
                    
                    extraction_groups[extraction_class].append(entity)
                
                processed = extraction_groups
                
            else:
                # Fallback for unexpected result format
                processed["extracted_items"] = [{
                    "value": str(results),
                    "sources": [{"start": 0, "end": min(100, len(original_text)), "text": original_text[:100] + "..."}]
                }]
                
        except Exception as e:
            logger.warning(f"Error processing langextract results: {e}")
            # Simple fallback
            processed["extracted_items"] = [{
                "value": f"Extraction completed (processing error: {str(e)})",
                "sources": [{"start": 0, "end": min(100, len(original_text)), "text": original_text[:100] + "..."}]
            }]
        
        return processed

    async def _store_results_in_s3(self, _results: dict[str, Any], _original_text: str) -> None:
        """Store extraction results in S3 for later retrieval."""
        # Temporarily disabled to avoid circular imports
        # try:
        #     # Create a unique key for this extraction
        #     extraction_id = str(uuid.uuid4())
            
        #     # Store structured results
        #     results_key = f"langextract/results/{extraction_id}.json"
        #     await s3_service.upload_json_object(results, results_key)
            
        #     # Store original text for reference
        #     text_key = f"langextract/source/{extraction_id}.txt"
        #     await s3_service.upload_text_object(original_text, text_key)
            
        #     # Add S3 references to results
        #     results["s3_results_key"] = results_key
        #     results["s3_source_key"] = text_key
            
        #     logger.info(f"Stored Langextract results in S3: {results_key}")
            
        # except Exception as e:
        #     logger.warning(f"Failed to store results in S3: {str(e)}")
        #     # Don't fail the entire extraction if S3 storage fails
        pass

    async def process_extraction_with_file_data(self, file_content: bytes, params: dict[str, Any]) -> dict[str, Any]:
        """
        Process data extraction with direct file content.
        
        Args:
            file_content: Binary file content
            params: Extraction parameters
            
        Returns:
            Extraction results
        """
        # Add file content to params
        extraction_params = {**params, "file_content": file_content}
        
        return await self.extract_structured_data(extraction_params)


# Global service instance
langextract_service = LangextractService()