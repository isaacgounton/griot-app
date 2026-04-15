import os
import json
import re
import logging
from typing import Dict, Any, Tuple, Union
from openai import OpenAI
from app.utils.ai_context import get_current_context
from app.services.ai.unified_ai_service import unified_ai_service

logger = logging.getLogger(__name__)

try:
    from app.services.research.news_research_service import news_research_service
    NEWS_RESEARCH_AVAILABLE = True
except ImportError:
    news_research_service = None
    NEWS_RESEARCH_AVAILABLE = False


class AIScriptGenerator:
    """AI script generation service supporting multiple providers with automatic fallback."""

    def __init__(self):
        self.unified_service = unified_ai_service
    
    def _get_script_prompt(self, script_type: str, max_duration: int, target_words: int, language: str = "english") -> str:
        """Generate enhanced prompts for natural speech patterns and conversational scripts."""
        language_name = language.title() if language.lower() != "english" else "English"
        language_instruction = f" Write the entire script in {language_name}." if language.lower() != "english" else ""
        
        # Enhanced conversational writing rules based on TypeScript ResearchService
        base_intro = f"""**CRITICAL LANGUAGE REQUIREMENT: You MUST write the entire script in {language_name}. Do NOT write in English or any other language. The script must be completely in {language_name} from start to finish.**

CRITICAL TOPIC ADHERENCE RULES:
1. Treat the topic as the CORE MESSAGE — your script must carry and amplify this exact perspective
2. The script must stand on the SAME SIDE as the topic — reinforce it, deepen it, live inside it
3. Open the script by stepping directly into the emotional world the topic inhabits — no introduction, no setup
4. Every sentence builds on the topic's viewpoint — bring evidence, stories, human truths that strengthen it
5. The script is a declaration, not a debate — write with conviction, not analysis
6. If the topic is specific (e.g., "ocean facts"), stay fully focused on that subject throughout
7. Build toward a complete, cohesive script that feels genuinely authored, not derived

CRITICAL CONVERSATIONAL WRITING RULES:
1. Write text that sounds NATURAL when spoken aloud by a voice-over artist
2. Use contractions (don't, can't, it's, we're) to sound more natural
3. Avoid written text phrases like "this video", "we will explore", "in this section"
4. Write as if you're talking directly to someone, not presenting information
5. Use spoken language patterns with authentic emotional depth
6. AVOID conversational fillers like "you know", "let me tell you", "right?", "like", "basically"
7. NO unnecessary excitement words like "literally", "totally", "honestly" unless truly needed
8. Remove redundant phrases like "here's the thing", "so get this", "wait for it"
9. For motivational/wisdom content: Write with profound emotional resonance, authenticity, and philosophical depth
10. Make it engaging and conversational through CONTENT, not through conversational crutches{language_instruction}

EMOTIONAL DEPTH & AUTHENTICITY (for motivation/life_wisdom):
- Touch the soul with universal truths about human experience
- Use authentic vulnerability to connect deeply with viewers
- Speak from real human struggles and hard-earned wisdom
- Include philosophical insights that resonate across cultures
- Weave in spiritual elements naturally when appropriate
- Use poetic, metaphorical language that creates emotional impact

SPEECH PATTERN EXAMPLES:
❌ BAD (Written style): "This video will show you {script_type}..."
❌ BAD (Over-conversational): "You know what? Let me tell you something crazy about {script_type}, right?"
✅ GOOD (Clean conversational): "This discovery about {script_type} will completely change your perspective."
✅ GOOD (Direct engagement): "{script_type} holds secrets that most people never discover."

TARGET: {target_words} words (approximately {max_duration} seconds when spoken naturally)

IMPORTANT: The user will provide a specific topic. Your entire script must be about that exact topic. Do not include generic content, introductions, or conclusions that don't directly relate to the user's topic.

{get_current_context()}"""
        
        if script_type == "facts":
            example = """
FACTS SCRIPT STYLE - Clean, Engaging Examples:
✅ GOOD: "Bananas are actually berries while strawberries aren't. A single cloud weighs over a million pounds - that's like having 100 elephants floating above your head. These facts will completely change how you see the world around you."

✅ GOOD: "Honey never spoils. Archaeologists found 3,000-year-old honey in Egyptian tombs that's still perfectly edible. Octopuses have three hearts and blue blood. Nature is more incredible than any science fiction story."

Focus on:
- Strong opening statements with surprising facts
- Clear, direct language without filler words
- Relatable comparisons to make facts memorable
- Build excitement through content, not conversational tags
- End with impact statements that reinforce amazement
        """
        elif script_type == "story":
            example = """
STORY SCRIPT STYLE - Direct Narrative Examples:
✅ GOOD: "This actually happened, and it's absolutely insane. A man disappears for 11 years, then shows up at his own funeral. Everyone's crying, his wife's devastated, and he just walks through the door like nothing happened."

✅ GOOD: "A stranger hands you a key on the street. No words, just a key. That's exactly what happened to Sarah, and what she found will haunt you forever."

Focus on:
- Immediate drama with strong opening hooks
- Present tense for urgency and immersion
- Direct storytelling without conversational interruptions
- Emotional hooks that create genuine suspense
- Clear, vivid imagery that paints the scene
        """
        elif script_type == "educational":
            example = """
EDUCATIONAL SCRIPT STYLE - Clear Instructional Examples:
✅ GOOD: "Your brain works like a computer, and this simple technique will upgrade its software forever. It takes just 30 seconds and will transform how you learn everything."

✅ GOOD: "Memory champions use one secret method that anyone can master. It's not talent - it's technique. Here's the exact process they follow to remember anything."

Focus on:
- Clear benefit statements without hype
- Simple analogies that clarify complex concepts
- Step-by-step approach with concrete outcomes
- Promise transformation through practical methods
- Direct instruction without unnecessary commentary
        """
        elif script_type == "motivation":
            example = """
MOTIVATIONAL SCRIPT STYLE - Deep, Authentic, Soul-Stirring Examples:

✅ PROFOUND WISDOM: "When you're angry, stay silent. Don't waste your time with explanations. Sometimes silence is the best way to cope with your emotions. People only hear what they want to hear, accept criticism, but never accept disrespect. The best way to respect yourself is to discipline yourself, persevere and never give up on something you truly believe in. It's difficult to wait, but it's more difficult to regret."

✅ AUTHENTIC VULNERABILITY: "You ever catch yourself staring at your phone, waiting for a text that never comes? That little hope lighting up your chest every time the screen flickers... only to fade when it's just another notification. I've been there. Sitting in the quiet, wondering why I'm not worth the effort. But here's what I learned: if someone wants to be in your life, they'll find a way."

✅ LIFE WISDOM: "Real love doesn't rush, it's not loud, it's not perfect, it's quiet support on your worst days. It's choosing each other, even when it's hard. It's the hand that holds yours when the world walks away. In a world full of temporary people, real love feels like peace, not chaos."

✅ SPIRITUAL DEPTH: "God sees what you don't say. He hears the prayers you whisper through your tears, and He understands the heaviness of your heart. Even when you smile, some nights you collapse in silence, yet you rise again the next day. This strength, He sees it, and He doesn't neglect your suffering; He's preparing something far greater than this pain."

✅ PERSONAL GROWTH: "Sometimes God puts a pause in your life, not to hold you back, but to equip you, shield you, and show you that His timing is flawless. Even when yours feels off, He's by your side, holding your hand, and softly saying, 'Don't be afraid. I'm here to guide you.' So, don't hurry through the journey. Embrace it."

✅ EMOTIONAL AUTHENTICITY: "You know what's one of the worst feelings in the world? Realizing that you didn't matter to someone as much as you thought you did. And then you start feeling stupid. Like you cared too much, like you gave too much of yourself to someone who didn't see it the same way. But here's what's crazy - you can love someone with every broken piece of your heart, even when they're the one who broke it."

Focus on:
- DEEP EMOTIONAL RESONANCE: Touch the soul, not just motivate surface-level action
- PHILOSOPHICAL INSIGHTS: Share profound truths about life, love, faith, relationships
- AUTHENTIC VULNERABILITY: Speak from real human experience and pain
- SPIRITUAL WISDOM: Weave in faith-based insights naturally (when appropriate)
- RELATIONSHIP WISDOM: Address love, trust, betrayal, and human connections
- PERSONAL REFLECTION: "You ever..." "Sometimes..." "Here's what I learned..."
- LIFE LESSONS: Hard-earned wisdom that comes from real experience
- EMOTIONAL VALIDATION: Acknowledge pain and struggle before offering hope
- POETIC LANGUAGE: Use beautiful, metaphorical expressions
- CONVERSATIONAL INTIMACY: Write like speaking to a close friend in private
- UNIVERSAL TRUTHS: Insights that transcend culture and resonate with everyone
        """
        elif script_type == "prayer":
            example = """
PRAYER/SPIRITUAL SCRIPT STYLE - Deep Faith-Based Examples:

✅ PROFOUND FAITH: "For I know the thoughts I have toward you, says the Lord, thoughts of peace and not of evil, to give you a future and a hope. You've faced tempests that nearly shattered you. You've wept in solitude. You've doubted your value, your calling, your tomorrow. The devil whispered that you're finished, that your life could never hold anything good. But God declares, I have a purpose for you."

✅ HEALING COMFORT: "God sees what you don't say. He hears the prayers you whisper through your tears, and He understands the heaviness of your heart. Even when you smile, some nights you collapse in silence, yet you rise again the next day. This strength, He sees it, and He doesn't neglect your suffering; He's preparing something far greater than this pain."

✅ DIVINE TIMING: "Sometimes God puts a pause in your life, not to hold you back, but to equip you, shield you, and show you that His timing is flawless. Even when yours feels off, He's by your side, holding your hand, and softly saying, 'Don't be afraid. I'm here to guide you.' So, don't hurry through the journey. Embrace it."

✅ SPIRITUAL VICTORY: "You prepare a table before me in the midst of my enemies. You anoint my head with oil, and my cup runs over. While they mocked, while they spread rumors, while they claimed you were finished, God was silently arranging a banquet, not just a small bite, but a grand feast, right in front of those who questioned you."

✅ FAITHFUL ENCOURAGEMENT: "God will make it happen. God will make it happen. I'm telling you, God will make it happen. He will fulfill His promises to you. He will provide. He will keep His word. Time might feel like it's working against you, but it can never overpower God's word. He is El Shaddai, the master and maker of time itself."

Focus on:
- BIBLICAL TRUTH: Weave in scripture naturally and authentically
- PERSONAL STRUGGLE: Acknowledge real pain and doubt before offering hope
- DIVINE CHARACTER: Emphasize God's faithfulness, love, and perfect timing
- SPIRITUAL WARFARE: Address the enemy's lies vs. God's truth
- PROPHETIC ENCOURAGEMENT: Speak life and destiny over viewers
- GENTLE COMFORT: Use tender, caring language for those who are hurting
- FAITH DECLARATIONS: Bold statements of God's power and promises
- INTIMATE RELATIONSHIP: Present God as personal, caring, and present
        """
        elif script_type == "pov":
            example = """
POV SCRIPT STYLE - Direct Immersive Examples:
✅ GOOD: "POV: You're texting your crush and they're typing for 10 minutes straight. Your heart's racing, you're overthinking everything, and then they just send 'k'. The audacity."

✅ GOOD: "POV: You're home alone and hear someone call your name. But you live alone. Your blood turns cold because you realize someone just used your actual name."

Focus on:
- Immediate immersion with POV setup
- Relatable emotions and physical reactions  
- Direct scenario description without commentary
- Strong ending that amplifies the situation
- Second-person perspective throughout
        """
        elif script_type == "conspiracy":
            example = """
CONSPIRACY/MYSTERY SCRIPT STYLE - Direct Revelation Examples:
✅ GOOD: "Declassified documents from 1947 reveal something that will make your blood run cold. The government has been hiding this for 75 years, but now we finally know the truth."

✅ GOOD: "That thing you learned in school? It never actually happened that way. What I'm about to show you will make you question everything you thought you knew about history."

Focus on:
- Immediate mystery with strong opening statements
- Personal stakes and emotional impact
- Shocking revelations backed by credible sources
- Question established narratives directly
- Build suspense through content, not conversational tags
        """
        elif script_type == "life_hacks":
            example = """
LIFE HACKS SCRIPT STYLE - Direct Solution Examples:
✅ GOOD: "This simple trick has changed my entire cooking routine. Put a wet paper towel under your cutting board and it will never slide around again. Takes 2 seconds and saves endless frustration."

✅ GOOD: "Struggling to open jars? Wrap a rubber band around the lid. It works every single time and requires zero extra strength."

Focus on:
- Personal discovery without excessive enthusiasm
- Instant practical solutions with clear benefits
- Specific timing and effort requirements
- Focus on the hack itself, not the revelation
- Direct problem-solution format
        """
        elif script_type == "would_you_rather":
            example = """
WOULD YOU RATHER SCRIPT STYLE - Direct Dilemma Examples:
✅ GOOD: "This is brutal. Would you rather know exactly when you're going to die, or how you're going to die? Knowing when means you can plan everything perfectly, but knowing how creates nothing but anxiety."

✅ GOOD: "Here's one that will mess with your head. Would you rather read everyone's thoughts but never turn it off, or be invisible but only when no one's looking? Both sound amazing until you really consider the consequences."

Focus on:
- Direct setup without excessive buildup
- Present impossible dilemmas with equal appeal
- Logical reasoning for each choice
- Encourage viewer engagement through genuine difficulty
- Clear presentation of the core conflict
        """
        elif script_type == "before_you_die":
            example = """
BEFORE YOU DIE SCRIPT STYLE - Direct Urgency Examples:
✅ GOOD: "Life is too short to keep putting this off. There are five experiences that will change you forever, and most people never have them. Don't be most people."

✅ GOOD: "The biggest regrets aren't about things you did, but things you were too scared to try. Here's what you absolutely cannot miss out on during your lifetime."

Focus on:
- Life urgency without melodrama
- FOMO motivation through clear statements
- Personal transformation promises
- Direct calls to action
- Focus on missed opportunities and regret prevention
        """
        elif script_type == "life_wisdom":
            example = """
LIFE WISDOM SCRIPT STYLE - Deep Philosophical Insights:

✅ PROFOUND INSIGHT: "Sometimes, it's better to leave things as they are. Let people go. Don't fight for closure. Don't ask for explanations. Don't run after answers. And don't wait for others to understand where you're coming from. Life taught me that peace isn't found in getting all the answers. It's found in letting go. So you can move forward without dragging the past behind you."

✅ RELATIONSHIP WISDOM: "Rule number one, without communication, there is no relationship. Without respect, there is no love. And without trust, there is no reason to continue. You don't notice a father's love until you look back and realize he was your silent shield the whole time. No loud words, no spotlight, just showing up every day, breaking behind the scenes so you could stay whole."

✅ EMOTIONAL AUTHENTICITY: "Have you ever pretended to be okay, just to avoid being asked what's wrong? You smile in public, but you collapse in silence. You give love even when your own heart is empty, and yet, no one notices. But listen, your silent battles matter. Your hidden strength is real. And one day, those who ignored your pain will regret not loving you as they should have."

✅ PERSONAL GROWTH: "You are not defined by your past or your struggles... you are defined by your resilience and the light you carry within you. Every step you take, no matter how small, is a victory. Every breath you take is a reminder that you're still here, still fighting, still growing."

✅ LETTING GO: "If love is a choice, then real love is choosing the same person. Even on the days it feels hardest to do so. But sometimes, loving means letting go, giving you the space to be with the one who truly makes you happy. Even if it means stepping away, my silence isn't the absence of love, it's my gift for your happiness."

Focus on:
- DEEP PHILOSOPHICAL TRUTHS: Universal insights about life, love, relationships
- EMOTIONAL VULNERABILITY: Authentic sharing of human struggles  
- WISE PERSPECTIVE: Hard-earned lessons from experience
- HEALING LANGUAGE: Words that comfort and validate pain
- GROWTH MINDSET: Encouraging resilience and personal development
- RELATIONSHIP INSIGHTS: Deep understanding of human connections
- SPIRITUAL UNDERTONES: Natural integration of faith and hope
- POETIC EXPRESSION: Beautiful, metaphorical language
        """
        elif script_type == "dark_psychology":
            example = """
DARK PSYCHOLOGY SCRIPT STYLE - Educational Awareness Examples:
✅ GOOD: "Someone has been using this technique on you your entire life, and you had no idea. It's called the foot-in-the-door technique, and once you recognize it, you can't ignore it."

✅ GOOD: "Some people seem to get whatever they want effortlessly. It's not charm - it's psychology. Here are three tactics they use that you need to recognize and defend against."

Focus on:
- Awareness revelation without sensationalism
- Educational protection rather than manipulation instruction
- Psychological insight with practical application
- Recognition patterns for viewer protection
- Ethical approach to psychological knowledge
        """
        elif script_type == "reddit_stories":
            example = """
REDDIT STORIES SCRIPT STYLE - Direct Personal Narrative Examples:
✅ GOOD: "This actually happened to me last week, and I'm still processing it. I discovered my roommate has been stealing my food for months. What I did next? Karma works in mysterious ways."

✅ GOOD: "I need to tell someone about this because it's been eating me alive. My best friend asked me to be her maid of honor, but she's marrying my ex."

Focus on:
- Personal authenticity without over-explanation
- Emotional investment through direct statements
- Relatable drama from real-life situations
- Engaging story structure with natural cliffhangers
- Honest emotional reactions to situations
        """
        elif script_type == "shower_thoughts":
            example = """
SHOWER THOUGHTS SCRIPT STYLE - Direct Mind-Bending Examples:
✅ GOOD: "If you're waiting for the waiter at a restaurant, doesn't that technically make you the waiter? Who's really serving whom here?"

✅ GOOD: "Every single photo of you is from the past. You've literally never seen yourself in real time. Your reflection is delayed by the speed of light."

Focus on:
- Mind-bending realizations without setup
- Philosophical questions that challenge assumptions
- Direct revelation of paradoxes
- Thought experiments that reframe ordinary experiences
- Simple statements with profound implications
        """
        elif script_type == "daily_news":
            example = """
        For daily news content, create informative and engaging news scripts with:
        - Current events and breaking news updates
        - Key facts and important developments
        - Clear, objective reporting style
        - Context and background information
        - Impact on viewers' daily lives
        - Credible sources and recent information
        - Professional news delivery tone
        Example: "Breaking: Major breakthrough in renewable energy as scientists achieve 47% solar panel efficiency. This could reduce your electricity bills by 60% within 5 years. Here's what this means for you..."
        """
        else:
            example = ""
        
        return f"""{base_intro}
        {example}
        
        You are now tasked with creating the best short script based on the user's requested topic.

        SCRIPT REQUIREMENTS:
        1. Create a COHESIVE, FLOWING script - not fragmented sentences
        2. Stay 100% focused on the user's specific topic throughout
        3. Make it engaging and conversational from start to finish
        4. Aim for approximately {target_words} words to fit within {max_duration} seconds
        5. Create content that works as ONE continuous narration, not separate scenes
        6. Include natural transitions between ideas within the topic

        IMPORTANT: Write the script as one flowing piece of content that tells a complete story or explanation about the topic. Do not write disconnected facts or sentences.

        CRITICAL JSON OUTPUT RULES:
        1. ONLY output a valid JSON object - no extra text before or after
        2. The "script" field must contain ONLY the spoken content - NO JSON syntax, brackets, or quotes
        3. Do NOT include any JSON formatting inside the script text itself
        4. The script should be pure conversational text that sounds natural when spoken aloud

        # Output Format (EXACT FORMAT REQUIRED)
        {{
            "title": "Catchy video title (max 60 characters)",
            "description": "Brief engaging description (max 150 characters)",
            "script": "The actual script content for TTS narration - write as one flowing, cohesive piece"
        }}
        """
    
    def _extract_structured_response(self, content: str) -> Dict[str, str]:
        """Extract structured response from AI response with robust error handling."""
        # Clean the content first - remove any non-JSON text before and after
        content = content.strip()
        
        try:
            # Try direct JSON parsing first
            parsed = json.loads(content)
            if "title" in parsed and "description" in parsed and "script" in parsed:
                # Clean the script to ensure it doesn't contain JSON artifacts
                clean_script = self._remove_json_artifacts(parsed["script"])
                return {
                    "title": parsed["title"],
                    "description": parsed["description"], 
                    "script": clean_script
                }
        except (json.JSONDecodeError, KeyError):
            pass
        
        try:
            # Try to find JSON object in the response
            json_start = content.find('{')
            json_end = content.rfind('}')
            if json_start != -1 and json_end != -1:
                json_content = content[json_start:json_end+1]
                parsed = json.loads(json_content)
                if "title" in parsed and "description" in parsed and "script" in parsed:
                    # Clean the script to ensure it doesn't contain JSON artifacts
                    clean_script = self._remove_json_artifacts(parsed["script"])
                    return {
                        "title": parsed["title"],
                        "description": parsed["description"], 
                        "script": clean_script
                    }
        except (json.JSONDecodeError, KeyError):
            pass
        
        # Fallback: try to extract from structured format (old format)
        try:
            title_match = re.search(r'TITRE\s*:\s*[«"]*([^»"\n]+)[»"]*', content, re.IGNORECASE)
            description_match = re.search(r'DESCRIPTION\s*:\s*[«"]*([^»"\n]+)[»"]*', content, re.IGNORECASE)
            script_match = re.search(r'SCRIPT\s*:\s*\n?(.*)', content, re.DOTALL | re.IGNORECASE)
            
            if script_match:
                return {
                    "title": title_match.group(1).strip() if title_match else "Generated Video",
                    "description": description_match.group(1).strip() if description_match else "AI-generated content",
                    "script": script_match.group(1).strip()
                }
        except Exception:
            pass
        
        # If all else fails, treat entire content as script
        cleaned_script = self._clean_conversational_script(content.strip())
        # Remove any JSON artifacts from the fallback script
        cleaned_script = self._remove_json_artifacts(cleaned_script)
        return {
            "title": "Generated Video",
            "description": "AI-generated content", 
            "script": cleaned_script
        }
    
    def _clean_conversational_script(self, script: str) -> str:
        """Clean script to ensure it follows conversational speech patterns without fillers."""
        import re
        
        # Remove common written text patterns that don't sound natural when spoken
        patterns_to_remove = [
            r'\b(this video|this content|in this video|in this section)\b',
            r'\b(we will explore|we will examine|we will discuss)\b',
            r'\b(let us|let\'s explore|let\'s examine)\b',
            r'\b(today we|today I will)\b',
            r'\b(welcome to|thanks for watching)\b'
        ]
        
        # Remove excessive conversational fillers
        conversational_fillers = [
            r'\b(you know what\?|you know,|you know)\b',
            r'\b(let me tell you|I\'m telling you)\b',
            r'\b(right\?|am I right\?)\b',
            r'\b(like,|basically,|honestly,|literally)\b',
            r'\b(here\'s the thing|so get this|wait for it)\b',
            r'\b(I mean,|I\'m not kidding|I\'m serious)\b',
            r'\b(trust me,|believe me,)\b'
        ]
        
        cleaned = script
        
        # Remove written text patterns first
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Remove conversational fillers
        for pattern in conversational_fillers:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Fix common issues
        cleaned = re.sub(r'\s+', ' ', cleaned)  # Multiple spaces
        cleaned = re.sub(r'^\s*[,\.]\s*', '', cleaned)  # Leading punctuation
        cleaned = re.sub(r',\s*,', ',', cleaned)  # Double commas from removal
        cleaned = cleaned.strip()
        
        return cleaned
    
    def _remove_json_artifacts(self, script: str) -> str:
        """Remove JSON artifacts and malformed JSON from script content."""
        import re
        
        # Remove JSON-like patterns that might appear in script
        # Remove curly braces with content that looks like JSON
        script = re.sub(r'\{[^}]*"[^"]*"[^}]*\}', '', script)
        
        # Remove standalone JSON keys like "title":", "description":", "script":
        script = re.sub(r'["\']?(?:title|description|script)["\']?\s*:', '', script, flags=re.IGNORECASE)
        
        # Remove JSON brackets and quotes at start/end
        script = re.sub(r'^[\s\{\["\'\_\-]*', '', script)
        script = re.sub(r'[\s\}\]"\'\_\-]*$', '', script)
        
        # Remove escaped quotes and newlines
        script = script.replace('\\n', ' ').replace('\\"', '"').replace("\\", "")
        
        # Remove multiple spaces and clean up
        script = re.sub(r'\s+', ' ', script).strip()
        
        return script
    
    def _count_words(self, text: str) -> int:
        """Count words in text."""
        return len(text.split())
    
    def _estimate_duration(self, word_count: int, speaking_rate: float = 2.8, 
                          tts_speed: float = 1.0, script_type: str = "facts") -> float:
        """
        Estimate duration based on word count, speaking rate, TTS speed, and script type.
        
        Args:
            word_count: Number of words in script
            speaking_rate: Base words per second (default 2.8)
            tts_speed: TTS speed multiplier (0.5-2.0, default 1.0)
            script_type: Type of script affecting pacing
        """
        # Adjust base speaking rate for script type
        script_adjustments = {
            "conspiracy": 0.7,      # More dramatic pauses, slower delivery
            "story": 0.8,           # Narrative pacing with pauses
            "motivation": 0.75,     # Emphasis and inspiration pauses
            "dark_psychology": 0.7, # Dramatic, slower delivery
            "prayer": 0.6,          # Very slow, reverent pace
            "facts": 1.0,           # Standard pace
            "educational": 0.9,     # Slightly slower for clarity
            "life_hacks": 1.1,      # Faster, energetic pace
            "would_you_rather": 0.8 # Pauses for thinking
        }
        
        # Apply script type adjustment
        script_multiplier = script_adjustments.get(script_type, 1.0)
        adjusted_rate = speaking_rate * script_multiplier
        
        # Apply TTS speed (inverse relationship - slower speed = longer duration)
        speed_adjusted_rate = adjusted_rate * tts_speed
        
        # Calculate base duration
        base_duration = word_count / speed_adjusted_rate
        
        # Add extra time for punctuation and natural pauses
        # Estimate 0.3s per sentence (rough count by periods/exclamations)
        estimated_sentences = max(1, word_count // 12)  # ~12 words per sentence
        pause_time = estimated_sentences * 0.3
        
        total_duration = base_duration + pause_time
        
        return total_duration
    
    async def generate_script(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate an AI script based on the provided parameters.
        
        Args:
            params: Dictionary containing:
                - topic: The topic for script generation
                - provider: AI provider preference ('auto', 'openai', 'groq')
                - script_type: Type of script ('facts', 'story', 'educational')
                - max_duration: Maximum duration in seconds
                - target_words: Target word count
                - language: Output language (default: 'english')
        
        Returns:
            Dictionary containing the generated script and metadata
        """
        topic = params.get('topic')
        provider = params.get('provider', 'auto')
        script_type = params.get('script_type', 'facts')
        max_duration = params.get('max_duration', 60)
        # Calculate target words based on duration if not provided
        if 'target_words' not in params:
            target_words = max(200, int(max_duration * 2.8))  # 2.8 words per second
        else:
            target_words = params.get('target_words', 200)
        language = params.get('language', 'english')
        
        if not topic:
            raise ValueError("Topic is required for script generation")
        
        # Validate and ensure topic is a string
        if not isinstance(topic, str):
            if isinstance(topic, dict) and 'topic' in topic:
                topic = topic['topic']
            else:
                topic = str(topic)
        if not topic.strip():
            raise ValueError("Topic cannot be empty")
        
        logger.debug(f"Validated topic: '{topic}' (type: {type(topic)})")
        
        # For daily news scripts, research current information
        news_context = ""
        if script_type == "daily_news" and NEWS_RESEARCH_AVAILABLE and news_research_service:
            try:
                research_results = await news_research_service.research_topic(topic)
                if research_results.get('summary'):
                    news_context = f"\n\nCurrent news context:\n{research_results['summary']}"
            except Exception as e:
                logger.warning(f"News research failed, proceeding without context: {e}")

        # Generate the prompt with language support
        prompt = self._get_script_prompt(script_type, max_duration, target_words, language)

        # Combine topic with news context for daily_news scripts
        user_content = topic + news_context if news_context else topic

        # Ensure user_content is a string (final safety check)
        if not isinstance(user_content, str):
            user_content = str(user_content)

        # Log request details
        logger.debug(f"System prompt length: {len(prompt)}, User content length: {len(user_content)}")
        logger.debug(f"Topic: '{topic}', Script type: '{script_type}', Language: '{language}', Preferred provider: '{provider}'")

        # Check for potentially problematic content
        if len(user_content) > 8000:
            logger.warning(f"User content is very long ({len(user_content)} chars), might cause API issues")
        if len(prompt) > 8000:
            logger.warning(f"System prompt is very long ({len(prompt)} chars), might cause API issues")

        # Use the unified AI service with automatic fallback
        try:
            response = await self.unified_service.create_chat_completion(
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_content}
                ],
                provider=provider,
                temperature=0.7
            )

            logger.info(f"Script generation successful with provider: {response['provider_used']}, model: {response['model_used']}")
            if response['fallback_used']:
                logger.warning(f"Fallback was used. Primary error: {response.get('primary_error', 'Unknown')}")

        except Exception as e:
            logger.error(f"All AI providers failed for script generation: {e}")
            raise

        # Extract structured response (title, description, script)
        content = response['content'] or ""
        structured_response = self._extract_structured_response(content)
        
        # Calculate metadata with context-aware duration estimation
        script_text = structured_response["script"]
        word_count = self._count_words(script_text)
        estimated_duration = self._estimate_duration(
            word_count=word_count,
            tts_speed=params.get('tts_speed', 1.0),
            script_type=script_type
        )
        
        return {
            "title": structured_response["title"],
            "description": structured_response["description"],
            "script": script_text,
            "word_count": word_count,
            "estimated_duration": estimated_duration,
            "provider_used": response.get('provider_used', 'unknown'),
            "model_used": response.get('model_used', 'unknown'),
            "fallback_used": response.get('fallback_used', False),
            "usage": response.get('usage', {})
        }


# Create a singleton instance
script_generator = AIScriptGenerator()