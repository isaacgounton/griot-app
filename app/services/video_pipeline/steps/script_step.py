"""Step 1: Script generation (topic discovery + script creation)."""
import logging
from app.services.video_pipeline.models import PipelineParams, ScriptResult
from app.services.video_pipeline.params import language_code_to_name, calculate_target_words
from app.services.text.script_generator import script_generator
from app.services.text.topic_discovery_service import topic_discovery_service

logger = logging.getLogger(__name__)


async def generate_script(params: PipelineParams) -> ScriptResult:
    """Generate or use custom script. Handles auto-topic discovery."""

    # Custom script shortcut
    if params.custom_script:
        logger.info("Using provided custom script")
        return ScriptResult(
            script_text=params.custom_script,
            word_count=len(params.custom_script.split()),
            topic_used=params.topic or "(custom)",
        )

    topic = params.topic

    # Auto-topic discovery
    if params.auto_topic and not topic:
        logger.info("Auto-topic discovery enabled")
        discovered = await topic_discovery_service.discover_topic(
            script_type=params.script_type,
            language=params.language,
        )
        if isinstance(discovered, dict) and 'topic' in discovered:
            topic = discovered['topic']
        elif isinstance(discovered, str):
            topic = discovered
        else:
            raise ValueError(f"Topic discovery returned invalid response: {discovered}")

        if not topic or not str(topic).strip():
            raise ValueError("Topic discovery returned empty topic")
        logger.info(f"Discovered topic: '{topic}'")

    if not topic:
        raise ValueError("No topic provided and auto_topic is not enabled")

    # Ensure topic is a clean string
    if isinstance(topic, dict):
        topic = topic.get('topic', str(topic))
    topic = str(topic).strip()
    if not topic:
        raise ValueError(f"Invalid topic: '{topic}'")

    # Generate script
    script_language = language_code_to_name(params.language)
    script_params = {
        'topic': topic,
        'provider': params.script_provider,
        'script_type': params.script_type,
        'max_duration': params.max_duration,
        'target_words': calculate_target_words(params.max_duration),
        'language': script_language,
    }

    logger.info(f"Generating script for topic: '{topic}' in {script_language}")
    result = await script_generator.generate_script(script_params)
    script_text = result.get('script', '')

    if not script_text:
        raise ValueError("Script generation returned empty content")

    logger.info(f"Generated script: {len(script_text)} chars, {len(script_text.split())} words")
    return ScriptResult(
        script_text=script_text,
        word_count=len(script_text.split()),
        topic_used=topic,
    )
