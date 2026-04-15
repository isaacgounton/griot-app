import os
import json
import logging
from typing import Dict, Any, List, Optional
from app.utils.ai_context import get_current_context
from app.services.ai.unified_ai_service import unified_ai_service

logger = logging.getLogger(__name__)


class ImagePromptGenerator:
    """Service for generating image prompts using AI models."""

    def __init__(self):
        self.unified_service = unified_ai_service

    def is_available(self) -> bool:
        """Check if the service is available."""
        return self.unified_service.is_available()

    async def generate_image_prompt_for_segment(
        self,
        script_text: str,
        full_script: str,
        segment_position: int,
        total_segments: int,
        model: str = "auto",
        search_query: str = None,
        semantics: dict = None
    ) -> str:
        """
        Generate an image prompt for a specific script segment.

        Args:
            script_text: The text content of this specific segment
            full_script: The complete script for context
            segment_position: Position of this segment (1-based)
            total_segments: Total number of segments
            model: Model preference (auto, openai, groq, etc.)
            search_query: Optional search query keywords for visual themes
            semantics: Optional semantic analysis (sentiment, domain, etc.)

        Returns:
            Generated image prompt suitable for Modal Image model
        """
        if not self.is_available():
            raise ValueError("AI provider not available")

        system_prompt = f"""You are an expert at creating image prompts for AI image generation models like Modal Image.

Your task is to generate compelling, visually striking image prompts that will create engaging visuals for video content.

{get_current_context()}

Guidelines:
1. Create vivid, descriptive prompts that capture the essence of the script segment
2. Include relevant style keywords (e.g., "cinematic", "photorealistic", "dramatic lighting")
3. Be specific about composition, colors, and visual elements
4. Keep prompts under 200 characters for optimal generation
5. Avoid text, words, or letters in the image
6. Focus on visual storytelling that complements the narration
7. Consider the segment's position in the overall story arc

Examples of good prompts:
- "Majestic underwater coral reef teeming with colorful fish, cinematic lighting, crystal clear water, National Geographic style"
- "Ancient stone temple in misty jungle, dramatic golden hour lighting, mysterious atmosphere, photorealistic"
- "Vast galaxy with swirling nebulae and bright stars, deep space photography, cosmic wonder, ultra detailed"

Generate a single image prompt that visually represents the content of this script segment."""

        # Build semantic context if available
        semantic_context = ""
        if semantics:
            semantic_context = f"""
SEMANTIC ANALYSIS:
- Sentiment: {semantics.get('sentiment', 'neutral')}
- Domain: {semantics.get('domain', 'general')}
- Time Period: {semantics.get('time_context', 'modern')}
- Location Type: {semantics.get('location_type', 'any')}
- Primary Action: {semantics.get('action_type', 'general')}
"""

        # Build search query context if available
        search_context = ""
        if search_query:
            search_context = f"""
SEARCH KEYWORDS: {search_query}
(These are key visual themes to incorporate)
"""

        user_prompt = f"""Create an AI image generation prompt for this video segment.

NARRATION TEXT:
"{script_text}"

FULL SCRIPT CONTEXT:
"{full_script[:500]}..."
{semantic_context}{search_context}
SEGMENT POSITION: {segment_position} of {total_segments}

CRITICAL REQUIREMENTS:
1. Create visuals that DIRECTLY illustrate what the narrator is describing
2. Match the emotional tone (sentiment: {semantics.get('sentiment', 'neutral') if semantics else 'neutral'})
3. Include specific visual elements mentioned in the narration text
4. Use the search keywords as visual themes{' (' + search_query + ')' if search_query else ''}
5. Style: Cinematic, photorealistic, professional, {semantics.get('time_context', 'modern') if semantics else 'modern'} era
6. No text/words in the image
7. Ensure visual coherence with the overall video narrative

Generate a compelling image prompt (under 200 characters) that brings this narration to life visually."""

        try:
            response = await self.unified_service.create_chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                provider=model,
                temperature=0.7,
                max_tokens=150
            )

            content = response.get('content')
            if not content:
                raise Exception("Empty response from AI")
            prompt = content.strip()

            # Clean up the prompt (remove quotes, etc.)
            prompt = prompt.strip('"\'')

            logger.info(f"Generated image prompt for segment {segment_position}: {prompt[:50]}...")

            return prompt

        except Exception as e:
            logger.error(f"Error generating image prompt: {str(e)}")
            # Fallback to a simple prompt based on the text
            fallback_prompt = f"Visual representation of: {script_text[:100]}, cinematic style"
            logger.info(f"Using fallback prompt: {fallback_prompt}")
            return fallback_prompt

    async def generate_music_prompt(
        self,
        script_text: str,
        script_type: str = "facts",
        video_duration: float = 60.0,
        model: str = "auto"
    ) -> str:
        """
        Generate a music prompt based on the script content and type.

        Args:
            script_text: The complete script text
            script_type: Type of script (facts, story, educational, etc.)
            video_duration: Duration of the video in seconds
            model: Model preference (auto, openai, groq, etc.)

        Returns:
            Generated music prompt for background music generation
        """
        if not self.is_available():
            raise ValueError("AI provider not available")

        system_prompt = f"""You are an expert at creating music prompts for AI music generation.

Your task is to generate compelling prompts that will create appropriate background music for video content.

{get_current_context()}

Guidelines:
1. Consider the mood, tone, and energy of the script
2. Match the music style to the content type (educational, dramatic, uplifting, etc.)
3. Specify tempo, instruments, and musical style
4. Keep prompts concise but descriptive (under 100 words)
5. Avoid lyrics or vocals unless specifically needed
6. Consider the video duration for pacing

Examples of good music prompts:
- "Uplifting ambient electronic music with soft synth pads, gentle percussion, inspiring and educational tone"
- "Mysterious cinematic orchestral music with strings and subtle percussion, building tension, documentary style"
- "Calming nature-inspired ambient music with piano and soft strings, peaceful and meditative"

Generate a music prompt that complements the script content and type."""

        user_prompt = f"""Script content:
"{script_text[:500]}..."

Script type: {script_type}
Video duration: {video_duration} seconds

Generate an appropriate background music prompt for this content."""

        try:
            response = await self.unified_service.create_chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                provider=model,
                temperature=0.7,
                max_tokens=100
            )

            content = response.get('content')
            if not content:
                raise Exception("Empty response from AI")
            prompt = content.strip()

            logger.info(f"Generated music prompt: {prompt[:50]}...")

            return prompt

        except Exception as e:
            logger.error(f"Error generating music prompt: {str(e)}")
            # Fallback to a simple prompt based on script type
            fallback_prompts = {
                "facts": "Uplifting ambient music with soft synths, educational and inspiring tone",
                "story": "Cinematic orchestral music with emotional depth, storytelling atmosphere",
                "educational": "Calm ambient electronic music, focus-enhancing, learning-friendly",
                "motivation": "Energetic uplifting music with driving beat, inspirational and powerful",
                "conspiracy": "Dark mysterious ambient music with tension, investigative atmosphere"
            }
            fallback_prompt = fallback_prompts.get(script_type, "Calm ambient music with gentle melody")
            logger.info(f"Using fallback music prompt: {fallback_prompt}")
            return fallback_prompt

    async def generate_multiple_image_prompts(
        self,
        segments: List[Dict[str, Any]],
        full_script: str,
        model: str = "auto"
    ) -> List[str]:
        """
        Generate image prompts for multiple script segments.

        Args:
            segments: List of segment dictionaries with 'text' key
            full_script: The complete script for context
            model: Model preference

        Returns:
            List of generated image prompts
        """
        prompts = []
        total_segments = len(segments)

        for i, segment in enumerate(segments, 1):
            try:
                prompt = await self.generate_image_prompt_for_segment(
                    script_text=segment.get('text', ''),
                    full_script=full_script,
                    segment_position=i,
                    total_segments=total_segments,
                    model=model
                )
                prompts.append(prompt)
            except Exception as e:
                logger.error(f"Failed to generate prompt for segment {i}: {str(e)}")
                # Add a fallback prompt
                fallback = f"Visual representation of script segment {i}, cinematic style"
                prompts.append(fallback)

        logger.info(f"Generated {len(prompts)} image prompts for {total_segments} segments")

        return prompts

    async def generate_prompt(
        self,
        topic: str,
        style: str = "realistic",
        mood: Optional[str] = None,
        context: Optional[str] = None,
        model: str = "auto"
    ) -> Dict[str, Any]:
        """
        Generate an optimized image prompt for AI image generation.

        Args:
            topic: The main subject/topic for the image
            style: Desired artistic style
            mood: Emotional tone or atmosphere
            context: Additional context for the image
            model: Model preference

        Returns:
            Dictionary with prompt, style, and suggested parameters
        """
        if not self.is_available():
            # Return a simple fallback prompt
            prompt = f"{topic}, {style} style"
            if mood:
                prompt += f", {mood} mood"
            if context:
                prompt += f", {context}"

            return {
                "prompt": prompt,
                "style": style,
                "parameters": {
                    "steps": 20,
                    "cfg_scale": 7.0,
                    "width": 1024,
                    "height": 1024
                }
            }

        try:
            # Build the prompt for the AI model
            system_prompt = """You are an expert at creating detailed, effective prompts for AI image generation.
Create a highly detailed prompt that will produce excellent results from AI image models like Stable Diffusion, DALL-E, or Midjourney.

Focus on:
- Specific visual details and composition
- Lighting and mood
- Style and artistic elements
- Technical quality aspects
- Avoid generic terms, be very specific

Return a JSON object with:
- prompt: The detailed image generation prompt
- style: The artistic style used
- parameters: Suggested generation parameters (steps, cfg_scale, dimensions)"""

            user_prompt = f"Topic: {topic}\nStyle: {style}"
            if mood:
                user_prompt += f"\nMood: {mood}"
            if context:
                user_prompt += f"\nContext: {context}"

            response = await self.unified_service.create_chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                provider=model,
                temperature=0.7,
                max_tokens=500
            )

            content = response.get('content')
            if not content:
                raise Exception("Empty response from AI")

            content = content.strip()

            # Try to parse as JSON, fallback if not
            try:
                result = json.loads(content)
                return result
            except json.JSONDecodeError:
                # Fallback: use the content as the prompt
                return {
                    "prompt": content,
                    "style": style,
                    "parameters": {
                        "steps": 20,
                        "cfg_scale": 7.0,
                        "width": 1024,
                        "height": 1024
                    }
                }

        except Exception as e:
            logger.error(f"Error generating image prompt: {str(e)}")
            # Return a simple fallback
            prompt = f"{topic}, {style} style"
            if mood:
                prompt += f", {mood} mood"
            if context:
                prompt += f", {context}"

            return {
                "prompt": prompt,
                "style": style,
                "parameters": {
                    "steps": 20,
                    "cfg_scale": 7.0,
                    "width": 1024,
                    "height": 1024
                }
            }


# Global instance
image_prompt_generator = ImagePromptGenerator()
