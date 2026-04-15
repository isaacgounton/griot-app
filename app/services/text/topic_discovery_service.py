"""
Topic discovery service that automatically finds trending topics for content generation.
"""
import os
import logging
import random
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.services.research.news_research_service import news_research_service

logger = logging.getLogger(__name__)


class TopicDiscoveryService:
    """Service for discovering trending topics based on script_type."""
    
    def __init__(self):
        self.topic_categories = {
            "facts": [
                "amazing science discoveries",
                "incredible animal facts",
                "fascinating historical events",
                "mind-blowing space facts",
                "surprising human body facts",
                "weird food facts around the world",
                "unbelievable ocean mysteries",
                "strange weather phenomena",
                "incredible technology breakthroughs",
                "mysterious archaeological findings"
            ],
            "story": [
                "inspirational success stories",
                "mysterious disappearances",
                "incredible survival stories",
                "unexplained phenomena",
                "heartwarming rescue stories",
                "amazing comeback stories",
                "mysterious historical events",
                "incredible coincidences",
                "life-changing moments",
                "extraordinary human achievements"
            ],
            "educational": [
                "how the brain works",
                "understanding climate change",
                "basics of quantum physics",
                "financial literacy tips",
                "effective study techniques",
                "understanding artificial intelligence",
                "basics of nutrition science",
                "how economies work",
                "understanding renewable energy",
                "psychology of human behavior"
            ],
            "motivation": [
                "overcoming fear and anxiety",
                "building confidence daily",
                "achieving your dreams",
                "developing mental toughness",
                "morning routines of successful people",
                "turning failures into success",
                "building healthy habits",
                "finding your life purpose",
                "mastering self-discipline",
                "creating positive mindset"
            ],
            "life_hacks": [
                "productivity tips for busy people",
                "money-saving life hacks",
                "time management secrets",
                "cleaning hacks that work",
                "cooking tips and tricks",
                "travel hacks for smart travelers",
                "study hacks for students",
                "fitness hacks for beginners",
                "organization tips for your home",
                "technology shortcuts you should know"
            ],
            "would_you_rather": [
                "impossible choices dilemmas",
                "superpowers vs reality choices",
                "time travel scenarios",
                "money vs happiness decisions",
                "career vs family choices",
                "adventure vs comfort decisions",
                "past vs future scenarios",
                "fame vs privacy choices",
                "power vs knowledge decisions",
                "love vs success dilemmas"
            ],
            "conspiracy": [
                "unexplained government secrets",
                "mysterious corporate cover-ups",
                "hidden historical truths",
                "unexplained scientific phenomena",
                "mysterious disappearances of evidence",
                "suppressed technological innovations",
                "hidden connections between events",
                "unexplained natural phenomena",
                "mysterious ancient civilizations",
                "suppressed medical discoveries"
            ],
            "reddit_stories": [
                "workplace drama stories",
                "relationship advice stories",
                "family conflict stories",
                "friendship betrayal stories",
                "dating disaster stories",
                "roommate horror stories",
                "job interview experiences",
                "travel mishap stories",
                "social media drama",
                "life lesson stories"
            ],
            "life_wisdom": [
                "lessons about love and relationships",
                "wisdom about trust and betrayal",
                "understanding forgiveness and letting go",
                "insights about self-worth and respect",
                "philosophy of life and meaning",
                "wisdom about family and friendships",
                "understanding pain and healing",
                "lessons about time and patience",
                "insights about success and failure",
                "wisdom about faith and hope"
            ],
            "shower_thoughts": [
                "mind-bending realizations",
                "everyday life paradoxes",
                "philosophical questions",
                "weird language observations",
                "time and space thoughts",
                "society and culture insights",
                "technology impact thoughts",
                "human behavior observations",
                "reality perception ideas",
                "consciousness and existence thoughts"
            ],
            "before_you_die": [
                "life experiences everyone should have",
                "places you must visit",
                "skills everyone should learn",
                "books that change your perspective",
                "adventures worth taking",
                "people you should meet",
                "foods you must try",
                "lessons life teaches you",
                "moments that matter most",
                "things that truly matter in life"
            ],
            "dark_psychology": [
                "psychological manipulation tactics",
                "understanding toxic behavior",
                "recognizing gaslighting patterns",
                "social influence techniques",
                "body language secrets",
                "understanding narcissistic behavior",
                "psychological defense mechanisms",
                "cognitive biases that control us",
                "subconscious mind tricks",
                "power dynamics in relationships"
            ],
            "daily_news": [
                "latest technology breakthroughs",
                "current world events",
                "breaking science news",
                "trending social topics",
                "recent discoveries",
                "current affairs updates",
                "latest health research",
                "environmental news updates",
                "economic developments",
                "cultural trends and changes"
            ]
        }
    
    async def discover_topic(self, script_type: str = "facts", use_trending: bool = True, language: str = "en") -> Dict[str, Any]:
        """
        Discover a topic based on script_type and current trends.
        
        Args:
            script_type: Type of script to generate topic for
            use_trending: Whether to use trending/news data for topic discovery
            language: Language for topic discovery (e.g., 'en', 'fr', 'es')
            
        Returns:
            Dictionary containing discovered topic and metadata
        """
        try:
            # For daily_news type, always use news research
            if script_type == "daily_news" or (use_trending and script_type in ["facts", "story", "educational"]):
                return await self._discover_trending_topic(script_type, language)
            else:
                return self._discover_static_topic(script_type)
                
        except Exception as e:
            logger.error(f"Topic discovery failed: {e}")
            # Fallback to static topic
            return self._discover_static_topic(script_type)
    
    async def _discover_trending_topic(self, script_type: str, language: str = "en") -> Dict[str, Any]:
        """Discover trending topic using news research."""
        try:
            # Get base topics for the script type
            base_topics = self.topic_categories.get(script_type, self.topic_categories["facts"])
            
            # For daily_news, research current trends
            if script_type == "daily_news":
                if language != "en":
                    # Add language-specific trending queries
                    language_names = {
                        "fr": "French", "es": "Spanish", "de": "German", "it": "Italian",
                        "pt": "Portuguese", "ru": "Russian", "zh": "Chinese", "ja": "Japanese",
                        "ko": "Korean", "ar": "Arabic", "hi": "Hindi", "th": "Thai",
                        "vi": "Vietnamese", "pl": "Polish", "nl": "Dutch"
                    }
                    lang_name = language_names.get(language, f"language-{language}")
                    trending_queries = [
                        f"trending news today {lang_name}",
                        f"breaking news latest {lang_name}",
                        f"current events trending {lang_name}",
                        f"viral news stories {lang_name}",
                        f"popular news topics {lang_name}"
                    ]
                else:
                    trending_queries = [
                        "trending news today",
                        "breaking news latest",
                        "current events trending",
                        "viral news stories",
                        "popular news topics"
                    ]
                research_query = random.choice(trending_queries)
            else:
                # Combine script type with trending keywords
                base_topic = random.choice(base_topics)
                if language != "en":
                    language_names = {
                        "fr": "French", "es": "Spanish", "de": "German", "it": "Italian",
                        "pt": "Portuguese", "ru": "Russian", "zh": "Chinese", "ja": "Japanese",
                        "ko": "Korean", "ar": "Arabic", "hi": "Hindi", "th": "Thai",
                        "vi": "Vietnamese", "pl": "Polish", "nl": "Dutch"
                    }
                    lang_name = language_names.get(language, f"language-{language}")
                    research_query = f"latest {base_topic} trending news {lang_name}"
                else:
                    research_query = f"latest {base_topic} trending news"
            
            # Research the topic
            research_results = await news_research_service.research_topic(research_query, max_results=3)
            
            if research_results.get('articles') and len(research_results['articles']) > 0:
                # Extract topic from research results
                articles = research_results['articles']
                
                # Use the first article's title as inspiration for topic
                first_article = articles[0]
                article_title = first_article.get('title', '')
                article_content = first_article.get('snippet', '') or first_article.get('content', '')
                
                # Generate a topic based on the article
                if script_type == "daily_news":
                    topic = self._extract_news_topic(article_title, article_content, language)
                else:
                    topic = self._adapt_topic_to_script_type(article_title, article_content, script_type, language)
                
                return {
                    'topic': topic,
                    'source': 'trending',
                    'script_type': script_type,
                    'research_data': research_results,
                    'inspiration': {
                        'title': article_title,
                        'content': article_content[:200] + "..." if len(article_content) > 200 else article_content
                    }
                }
            else:
                # No trending data available, fallback to static
                logger.warning("No trending data available, using static topic")
                return self._discover_static_topic(script_type)
                
        except Exception as e:
            logger.error(f"Trending topic discovery failed: {e}")
            return self._discover_static_topic(script_type)
    
    def _discover_static_topic(self, script_type: str) -> Dict[str, Any]:
        """Discover topic from predefined categories."""
        topics = self.topic_categories.get(script_type, self.topic_categories["facts"])
        selected_topic = random.choice(topics)
        
        return {
            'topic': selected_topic,
            'source': 'static',
            'script_type': script_type,
            'category': script_type
        }
    
    def _extract_news_topic(self, title: str, content: str, language: str = "en") -> str:
        """Extract a concise topic from news article for daily_news script type."""
        # Clean up the title and extract key elements
        title_clean = title.replace(' - ', ' ').replace('|', '').strip()
        
        # Take the main part of the title (before any source attribution)
        main_title = title_clean.split(' - ')[0].split('|')[0].strip()
        
        # Add language context if not English
        if language != "en":
            # For non-English, we might want to request the topic be about content relevant to that language/region
            language_context = {
                "fr": "nouvelles en France",
                "es": "noticias en España", 
                "de": "Nachrichten in Deutschland",
                "it": "notizie in Italia",
                "pt": "notícias no Brasil",
                "zh": "中国新闻",
                "ja": "日本のニュース",
                "ko": "한국 뉴스"
            }
            context = language_context.get(language, f"news in {language}")
            return f"{main_title} - {context}"
        
        # If title is too long, extract key phrases
        if len(main_title) > 100:
            # Extract first meaningful sentence or phrase
            sentences = main_title.split('. ')
            main_title = sentences[0] if sentences else main_title[:100]
        
        return main_title
    
    def _adapt_topic_to_script_type(self, title: str, content: str, script_type: str, language: str = "en") -> str:
        """Adapt news article to fit specific script type."""
        # Extract key elements from title/content
        title_clean = title.replace(' - ', ' ').replace('|', '').strip()
        
        # Language-specific adaptations
        templates = {
            "en": {
                "facts": "fascinating facts about {topic}",
                "story": "the incredible story behind {topic}",
                "educational": "understanding {topic}",
                "motivation": "lessons we can learn from {topic}",
                "life_wisdom": "wisdom and insights about {topic}"
            },
            "fr": {
                "facts": "faits fascinants sur {topic}",
                "story": "l'histoire incroyable derrière {topic}",
                "educational": "comprendre {topic}",
                "motivation": "leçons que nous pouvons apprendre de {topic}",
                "life_wisdom": "sagesse et réflexions sur {topic}"
            },
            "es": {
                "facts": "datos fascinantes sobre {topic}",
                "story": "la historia increíble detrás de {topic}",
                "educational": "entendiendo {topic}",
                "motivation": "lecciones que podemos aprender de {topic}",
                "life_wisdom": "sabiduría y reflexiones sobre {topic}"
            },
            "de": {
                "facts": "faszinierende Fakten über {topic}",
                "story": "die unglaubliche Geschichte hinter {topic}",
                "educational": "{topic} verstehen",
                "motivation": "Lektionen, die wir von {topic} lernen können",
                "life_wisdom": "Weisheit und Einsichten über {topic}"
            }
        }
        
        # Get templates for the language, fallback to English
        lang_templates = templates.get(language, templates["en"])
        
        # Adapt based on script type
        if script_type == "facts":
            return lang_templates["facts"].format(topic=title_clean.lower())
        elif script_type == "story":
            return lang_templates["story"].format(topic=title_clean.lower())
        elif script_type == "educational":
            return lang_templates["educational"].format(topic=title_clean.lower())
        elif script_type == "motivation":
            return lang_templates["motivation"].format(topic=title_clean.lower())
        elif script_type == "life_wisdom":
            return lang_templates["life_wisdom"].format(topic=title_clean.lower())
        else:
            # For other types, return adapted title
            return title_clean
    
    def get_topic_keywords(self, topic: str, script_type: str) -> List[str]:
        """Generate keywords for video search based on discovered topic."""
        # Base keywords for script type
        script_keywords = {
            "facts": ["facts", "amazing", "incredible", "surprising", "mind-blowing"],
            "story": ["story", "narrative", "tale", "journey", "experience"],
            "educational": ["learn", "understand", "explain", "tutorial", "education"],
            "motivation": ["inspire", "motivate", "success", "achieve", "overcome"],
            "life_wisdom": ["wisdom", "insights", "lessons", "truth", "understanding"],
            "life_hacks": ["tips", "tricks", "hacks", "shortcuts", "efficient"],
            "daily_news": ["news", "current", "latest", "breaking", "update"]
        }
        
        # Get script-specific keywords
        base_keywords = script_keywords.get(script_type, ["interesting", "important"])
        
        # Extract topic words
        topic_words = [word.strip() for word in topic.lower().split() if len(word) > 3]
        
        # Combine and return
        return base_keywords + topic_words[:5]  # Limit topic words to avoid too many keywords
    
    async def discover_topics(
        self,
        keywords: str,
        category: Optional[str] = None,
        language: str = "en",
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Discover multiple trending topics based on keywords and category.

        Args:
            keywords: Keywords to search for topics
            category: Category filter (optional)
            language: Language code
            max_results: Maximum number of topics to return

        Returns:
            Dictionary with topics list, search query, and total found
        """
        try:
            # Use news research service to find trending topics
            if hasattr(news_research_service, 'search_trending_topics'):
                # If news service has topic search capability
                topics_data = await news_research_service.search_trending_topics(
                    keywords=keywords,
                    category=category,
                    language=language,
                    max_results=max_results
                )

                return {
                    "topics": topics_data.get("topics", []),
                    "search_query": keywords,
                    "total_found": len(topics_data.get("topics", []))
                }
            else:
                # Fallback: generate topics based on keywords
                topics = []
                keyword_list = [k.strip() for k in keywords.split() if k.strip()]

                # Generate topic variations
                for i in range(min(max_results, len(keyword_list) * 2)):
                    if i < len(keyword_list):
                        # Direct keyword topics
                        topics.append({
                            "title": f"The Impact of {keyword_list[i].title()}",
                            "description": f"Exploring the significance and effects of {keyword_list[i]} in modern society",
                            "category": category or "general",
                            "trending_score": random.randint(1, 100)
                        })
                    else:
                        # Combined keyword topics
                        idx1 = (i - len(keyword_list)) % len(keyword_list)
                        idx2 = (i - len(keyword_list) + 1) % len(keyword_list)
                        if idx1 != idx2:
                            topics.append({
                                "title": f"{keyword_list[idx1].title()} and {keyword_list[idx2].title()}: A Comprehensive Analysis",
                                "description": f"Understanding the relationship between {keyword_list[idx1]} and {keyword_list[idx2]}",
                                "category": category or "general",
                                "trending_score": random.randint(1, 100)
                            })

                return {
                    "topics": topics[:max_results],
                    "search_query": keywords,
                    "total_found": len(topics)
                }

        except Exception as e:
            logger.error(f"Error discovering topics: {str(e)}")
            # Return empty result on error
            return {
                "topics": [],
                "search_query": keywords,
                "total_found": 0
            }


# Singleton instance
topic_discovery_service = TopicDiscoveryService()