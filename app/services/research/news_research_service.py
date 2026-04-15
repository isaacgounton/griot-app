"""
Enhanced News research service using Google Search and Perplexity APIs for comprehensive news research.
"""
import os
import logging
import asyncio
import aiohttp
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv
from app.utils.ai_context import get_current_context

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class NewsResearchService:
    """Enhanced service for researching current news and events with comprehensive search capabilities."""
    
    def __init__(self):
        self.google_api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
        self.google_search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
        self.perplexity_api_key = os.getenv('PERPLEXITY_API_KEY')
        self.news_api_key = os.getenv('NEWS_API_KEY')
        
        # Use search-enabled Perplexity models for better results
        # Start with user-configured model, then fall back to defaults
        user_model = os.getenv('PERPLEXITY_MODEL', 'sonar')
        self.perplexity_search_models = [
            user_model,  # User's preferred model first
            'sonar-pro',
            'sonar-small-online',
            'sonar-medium-online',
            'sonar'
        ]
        # Remove duplicates while preserving order
        seen = set()
        self.perplexity_search_models = [x for x in self.perplexity_search_models if not (x in seen or seen.add(x))]
        
        # Validate at least one service is available
        available_services = []
        if self.google_api_key and self.google_search_engine_id:
            available_services.append("Google Search")
        if self.perplexity_api_key:
            available_services.append("Perplexity")
        if self.news_api_key:
            available_services.append("NewsAPI")
            
        if not available_services:
            logger.warning("No news research APIs configured. At least one API required for news research.")
        else:
            logger.info(f"News research initialized with: {', '.join(available_services)}")
    
    async def research_topic(self, topic: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Comprehensive research of a topic using multiple sources and enhanced search capabilities.
        
        Args:
            topic: Topic to research
            max_results: Maximum number of news articles to fetch per source
            
        Returns:
            Dictionary containing comprehensive research results from multiple sources
        """
        logger.info(f"Starting comprehensive research for topic: {topic}")
        all_results = {
            'articles': [],
            'summary': '',
            'sources_used': [],
            'research_date': datetime.now().isoformat(),
            'query_used': topic,
            'total_sources': 0
        }
        
        # Try to get results from multiple sources
        google_results = None
        perplexity_results = None
        newsapi_results = None
        
        try:
            # Try Google Search for news articles
            if self.google_api_key and self.google_search_engine_id:
                try:
                    google_results = await self._search_google_news_basic(topic, max_results)
                    if google_results and google_results.get('articles'):
                        all_results['articles'].extend(google_results['articles'])
                        all_results['sources_used'].append('Google Search API')
                        logger.info(f"Google Search found {len(google_results['articles'])} articles")
                except Exception as e:
                    logger.warning(f"Google Search failed: {e}")
            
            # Try NewsAPI for additional news coverage
            if self.news_api_key:
                try:
                    newsapi_results = await self._search_newsapi(topic, max_results)
                    if newsapi_results and newsapi_results.get('articles'):
                        all_results['articles'].extend(newsapi_results['articles'])
                        all_results['sources_used'].append('NewsAPI')
                        logger.info(f"NewsAPI found {len(newsapi_results['articles'])} articles")
                except Exception as e:
                    logger.warning(f"NewsAPI failed: {e}")
            
            # Use Perplexity for comprehensive analysis and additional sources
            if self.perplexity_api_key:
                try:
                    perplexity_results = await self._search_perplexity_enhanced(topic)
                    if perplexity_results:
                        # Add Perplexity's comprehensive analysis
                        if perplexity_results.get('articles'):
                            all_results['articles'].extend(perplexity_results['articles'])
                        all_results['sources_used'].append('Perplexity AI')
                        logger.info("Perplexity research completed successfully")
                except Exception as e:
                    logger.warning(f"Perplexity API failed: {e}")
            
            # Generate comprehensive summary from all sources
            all_results['summary'] = await self._generate_comprehensive_summary(
                all_results['articles'], topic, google_results, perplexity_results, newsapi_results
            )
            
            all_results['total_sources'] = len(all_results['sources_used'])
            
            if all_results['articles'] or all_results['summary']:
                logger.info(f"Research completed: {len(all_results['articles'])} articles from {len(all_results['sources_used'])} sources")
                return all_results
            
            # If no results from either source, return informative fallback
            logger.warning("No research results from any source, returning fallback")
            return self._generate_fallback_response(topic)
            
        except Exception as e:
            logger.error(f"Comprehensive research failed: {e}")
            return self._generate_error_response(topic, str(e))

    async def research_news(self, query: str, language: str = "en", max_results: int = 10,
                           sort_by: str = "relevance", time_range: Optional[str] = None) -> Dict[str, Any]:
        """
        Research news articles based on a query with enhanced filtering and current news focus.

        Args:
            query: Search query for news research
            language: Language code for results (default: en)
            max_results: Maximum number of results to return
            sort_by: Sort method - relevance, date, popularity
            time_range: Time range filter - day, week, month, year

        Returns:
            Dictionary containing news articles and metadata
        """
        import time
        start_time = time.time()

        logger.info(f"Starting news research for query: '{query}' with max_results: {max_results}")

        all_articles = []
        sources_used = []

        try:
            # Calculate date range based on time_range parameter
            date_restrict = self._calculate_date_restrict(time_range)

            # Try Google Search first for most recent news
            if self.google_api_key and self.google_search_engine_id:
                try:
                    google_results = await self._search_google_news_enhanced(query, max_results, date_restrict, language)
                    if google_results and google_results.get('articles'):
                        all_articles.extend(google_results['articles'])
                        sources_used.append('Google Search API')
                        logger.info(f"Google Search found {len(google_results['articles'])} articles")
                except Exception as e:
                    logger.warning(f"Google Search failed: {e}")

            # Try NewsAPI for additional coverage
            if self.news_api_key and len(all_articles) < max_results:
                try:
                    newsapi_results = await self._search_newsapi_enhanced(query, max_results - len(all_articles), time_range, language)
                    if newsapi_results and newsapi_results.get('articles'):
                        all_articles.extend(newsapi_results['articles'])
                        sources_used.append('NewsAPI')
                        logger.info(f"NewsAPI found {len(newsapi_results['articles'])} articles")
                except Exception as e:
                    logger.warning(f"NewsAPI failed: {e}")

            # Try Perplexity for comprehensive analysis if we still need more results
            if self.perplexity_api_key and len(all_articles) < max_results:
                try:
                    perplexity_results = await self._search_perplexity_news(query, max_results - len(all_articles))
                    if perplexity_results and perplexity_results.get('articles'):
                        all_articles.extend(perplexity_results['articles'])
                        sources_used.append('Perplexity AI')
                        logger.info(f"Perplexity found {len(perplexity_results['articles'])} articles")
                except Exception as e:
                    logger.warning(f"Perplexity failed: {e}")

            # Remove duplicates and filter by date
            all_articles = self._filter_and_deduplicate_articles(all_articles, max_results)

            # Sort articles based on sort_by parameter
            all_articles = self._sort_articles(all_articles, sort_by)

            # Ensure we don't exceed max_results
            all_articles = all_articles[:max_results]

            search_time = time.time() - start_time

            result = {
                "articles": all_articles,
                "total_results": len(all_articles),
                "search_query": query,
                "search_time": search_time,
                "sources_used": sources_used,
                "language": language,
                "sort_by": sort_by,
                "time_range": time_range,
                "date_restrict_used": date_restrict
            }

            logger.info(f"News research completed: {len(all_articles)} articles from {len(sources_used)} sources in {search_time:.2f}s")
            return result

        except Exception as e:
            logger.error(f"News research failed: {e}")
            search_time = time.time() - start_time
            return {
                "articles": [],
                "total_results": 0,
                "search_query": query,
                "search_time": search_time,
                "error": str(e),
                "sources_used": []
            }

    def _calculate_date_restrict(self, time_range: Optional[str]) -> str:
        """Calculate Google Search date restrict parameter based on time_range."""
        if not time_range:
            return "d7"  # Default to last 7 days for current news

        time_range_map = {
            "day": "d1",
            "week": "d7",
            "month": "d30",
            "year": "d365"
        }

        return time_range_map.get(time_range.lower(), "d7")

    async def _search_google_news_enhanced(self, query: str, max_results: int, date_restrict: str = "d7",
                                          language: str = "en") -> Dict[str, Any]:
        """Enhanced Google Search for recent news articles with better date filtering."""
        logger.info(f"Starting enhanced Google Search for: '{query}' with date_restrict: {date_restrict}")

        # Enhanced search queries for current news
        search_queries = [
            f"{query} news",
            f'"{query}" latest news',
            f"{query} breaking news",
            f"{query} recent developments"
        ]

        all_articles = []

        for query_variant in search_queries[:2]:  # Try top 2 queries to avoid rate limits
            try:
                url = "https://www.googleapis.com/customsearch/v1"
                params = {
                    'key': self.google_api_key,
                    'cx': self.google_search_engine_id,
                    'q': query_variant,
                    'num': min(8, max_results),  # Get more per query for better filtering
                    'dateRestrict': date_restrict,
                    'sort': 'date',  # Sort by date, most recent first
                    'lr': f'lang_{language}',
                    # Restrict to major news sources
                    'siteSearch': ('reuters.com OR bbc.com OR cnn.com OR apnews.com OR npr.org OR '
                                 'nbcnews.com OR abcnews.go.com OR cbsnews.com OR bloomberg.com OR '
                                 'wsj.com OR nytimes.com OR washingtonpost.com OR theguardian.com'),
                    'tbm': 'nws'  # News search
                }

                logger.info(f"Google Search params: {params}")

                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            items = data.get('items', [])
                            logger.info(f"Google Search returned {len(items)} items for query: {query_variant}")

                            for item in items:
                                article = self._parse_google_article(item, query_variant)
                                if article:
                                    # Additional date validation
                                    if self._is_recent_article(article, date_restrict):
                                        all_articles.append(article)
                                        logger.debug(f"Added article: {article['title'][:50]}... from {article.get('published_at', 'unknown date')}")

                        else:
                            error_text = await response.text()
                            logger.warning(f"Google Search API returned {response.status} for query: {query_variant}: {error_text}")

            except Exception as e:
                logger.warning(f"Google Search query '{query_variant}' failed: {e}")
                continue

        # Remove duplicates and sort by date
        all_articles = self._deduplicate_articles(all_articles)
        all_articles = sorted(all_articles, key=lambda x: x.get('published_at', ''), reverse=True)

        logger.info(f"Google Search found {len(all_articles)} valid articles after filtering")

        return {
            'articles': all_articles[:max_results],
            'source': 'google_search',
            'total_found': len(all_articles)
        }

    def _parse_google_article(self, item: Dict[str, Any], search_query: str) -> Optional[Dict[str, Any]]:
        """Parse a Google Search result into a standardized article format."""
        try:
            title = item.get('title', '').replace(' - ', ' | ').strip()
            snippet = item.get('snippet', '').strip()
            link = item.get('link', '').strip()

            if not title or not link:
                return None

            # Extract date from various possible fields
            published_at = self._extract_date_from_item(item)

            # Extract source from display link
            display_link = item.get('displayLink', '')
            source = self._extract_source_from_display_link(display_link)

            return {
                'title': title,
                'description': snippet,
                'url': link,
                'source': source,
                'published_at': published_at,
                'search_query': search_query,
                'provider': 'google_search'
            }

        except Exception as e:
            logger.warning(f"Failed to parse Google article: {e}")
            return None

    def _extract_date_from_item(self, item: Dict[str, Any]) -> str:
        """Extract publication date from Google Search item with improved parsing."""
        import re

        # Try different date fields in structured data
        possible_date_fields = ['pagemap', 'metatags', 'newsarticle', 'article', 'webpage']

        for field in possible_date_fields:
            if field in item:
                data = item[field]
                if isinstance(data, list) and data:
                    data = data[0]

                # Look for date fields
                date_keys = ['datepublished', 'publishdate', 'date', 'pubdate', 'created_at',
                           'datecreated', 'datemodified', 'lastmodified', 'newsdate']
                for key in date_keys:
                    if key in data and data[key]:
                        date_str = str(data[key]).strip()
                        try:
                            # Handle various date formats
                            if 'T' in date_str:
                                # ISO format
                                date_str = date_str.split('T')[0]
                            elif '/' in date_str:
                                # Try to parse MM/DD/YYYY or DD/MM/YYYY
                                pass
                            elif len(date_str) == 10 and date_str.count('-') == 2:
                                # Already in YYYY-MM-DD format
                                pass
                            else:
                                # Try to extract date from string
                                continue

                            # Validate the date
                            datetime.strptime(date_str, '%Y-%m-%d')
                            return date_str
                        except:
                            continue

        # Try to extract date from title or snippet
        title = item.get('title', '')
        snippet = item.get('snippet', '')

        # Look for date patterns in title/snippet
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
            r'(\d{2}/\d{2}/\d{4})',  # MM/DD/YYYY
            r'(\d{2}-\d{2}-\d{4})',  # DD-MM-YYYY
        ]

        for text in [title, snippet]:
            for pattern in date_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    try:
                        # Normalize to YYYY-MM-DD
                        if '/' in match:
                            parts = match.split('/')
                            if len(parts) == 3:
                                # Assume MM/DD/YYYY format
                                month, day, year = parts
                                date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        elif '-' in match:
                            parts = match.split('-')
                            if len(parts) == 3:
                                if len(parts[0]) == 4:  # YYYY-MM-DD
                                    date_str = match
                                else:  # DD-MM-YYYY
                                    day, month, year = parts
                                    date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"

                        # Validate and check if recent
                        datetime.strptime(date_str, '%Y-%m-%d')
                        parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                        if parsed_date > datetime.now() - timedelta(days=365):  # Within last year
                            return date_str
                    except:
                        continue

        # If no date found, assume it's recent (today)
        logger.debug(f"No date found for article: {title[:50]}...")
        return datetime.now().strftime('%Y-%m-%d')

    def _extract_source_from_display_link(self, display_link: str) -> str:
        """Extract clean source name from display link."""
        if not display_link:
            return "Unknown"

        # Remove www. prefix
        source = display_link.replace('www.', '')

        # Common source mappings
        source_map = {
            'bbc.com': 'BBC News',
            'bbc.co.uk': 'BBC News',
            'reuters.com': 'Reuters',
            'apnews.com': 'Associated Press',
            'cnn.com': 'CNN',
            'nytimes.com': 'New York Times',
            'washingtonpost.com': 'Washington Post',
            'foxnews.com': 'Fox News',
            'nbcnews.com': 'NBC News',
            'abcnews.go.com': 'ABC News',
            'cbsnews.com': 'CBS News',
            'npr.org': 'NPR',
            'bloomberg.com': 'Bloomberg',
            'wsj.com': 'Wall Street Journal',
            'theguardian.com': 'The Guardian',
            'news.google.com': 'Google News'
        }

        return source_map.get(source, source.title())

    def _is_recent_article(self, article: Dict[str, Any], date_restrict: str) -> bool:
        """Check if article is recent enough based on date_restrict."""
        try:
            published_date = article.get('published_at', '')
            if not published_date:
                return True  # Include if no date available

            # Parse date
            if 'T' in published_date:
                published_date = published_date.split('T')[0]

            article_date = datetime.strptime(published_date, '%Y-%m-%d')

            # Calculate cutoff date based on date_restrict
            days_map = {
                'd1': 1,
                'd7': 7,
                'd30': 30,
                'd365': 365
            }

            days = days_map.get(date_restrict, 7)
            cutoff_date = datetime.now() - timedelta(days=days)

            return article_date >= cutoff_date

        except Exception as e:
            logger.warning(f"Failed to check article date: {e}")
            return True  # Include if date parsing fails

    async def _search_newsapi_enhanced(self, query: str, max_results: int, time_range: Optional[str] = None,
                                     language: str = "en") -> Dict[str, Any]:
        """Enhanced NewsAPI search with better date filtering."""
        logger.info(f"Starting enhanced NewsAPI search for: '{query}'")

        try:
            # Calculate date range
            if time_range:
                days_map = {'day': 1, 'week': 7, 'month': 30, 'year': 365}
                days = days_map.get(time_range.lower(), 7)
            else:
                days = 7  # Default to 7 days

            from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

            url = "https://newsapi.org/v2/everything"
            params = {
                'apiKey': self.news_api_key,
                'q': query,
                'from': from_date,
                'sortBy': 'publishedAt',
                'pageSize': min(max_results, 20),
                'language': language
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        articles = []
                        for article in data.get('articles', []):
                            if not article.get('title') or not article.get('description'):
                                continue

                            # Parse published date
                            published_at = article.get('publishedAt', '')
                            if published_at:
                                try:
                                    # Convert ISO format to date string
                                    dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                                    published_at = dt.strftime('%Y-%m-%d')
                                except:
                                    published_at = datetime.now().strftime('%Y-%m-%d')

                            news_article = {
                                'title': article['title'],
                                'description': article.get('description', ''),
                                'url': article.get('url', ''),
                                'source': article.get('source', {}).get('name', 'NewsAPI'),
                                'published_at': published_at,
                                'provider': 'newsapi'
                            }

                            articles.append(news_article)

                        # Sort by date (most recent first)
                        articles = sorted(articles, key=lambda x: x.get('published_at', ''), reverse=True)

                        logger.info(f"NewsAPI found {len(articles)} articles")
                        return {
                            'articles': articles,
                            'source': 'newsapi',
                            'total_found': len(articles)
                        }

                    else:
                        error_text = await response.text()
                        logger.warning(f"NewsAPI returned {response.status}: {error_text}")
                        return {'articles': [], 'source': 'newsapi', 'total_found': 0}

        except Exception as e:
            logger.warning(f"NewsAPI search failed: {e}")
            return {'articles': [], 'source': 'newsapi', 'total_found': 0}

    async def _search_perplexity_news(self, query: str, max_results: int) -> Dict[str, Any]:
        """Search Perplexity for news articles with current date context."""
        logger.info(f"Starting Perplexity news search for: '{query}'")

        try:
            url = "https://api.perplexity.ai/chat/completions"
            headers = {
                'Authorization': f'Bearer {self.perplexity_api_key}',
                'Content-Type': 'application/json'
            }

            # Get current date/time context
            current_context = get_current_context()
            
            prompt = f"""Find {max_results} recent news articles about: {query}

{current_context}

Please provide the results in this exact JSON format:
{{
  "articles": [
    {{
      "title": "Article title",
      "description": "Brief description",
      "url": "https://example.com/article",
      "source": "News Source Name",
      "published_at": "2025-01-15"
    }}
  ]
}}

Important: Only include articles published AFTER January 1, 2024. Focus on articles from the last few weeks.
Focus on credible news sources only."""

            data = {
                'model': os.getenv('PERPLEXITY_MODEL', 'sonar-pro'),
                'messages': [
                    {
                        'role': 'system',
                        'content': f"""You are a news research specialist. Today's date is {current_context}. 
Always provide the most current and recent information available. 
Focus on news from 2024-2025, especially recent developments from the past few weeks.
Never provide information from before 2024 unless specifically about historical context.
Prioritize recent, relevant, and factual information."""
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'max_tokens': 2000
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result['choices'][0]['message']['content']

                        # Try to parse JSON from response
                        try:
                            # Find JSON in the response
                            json_start = content.find('{')
                            json_end = content.rfind('}') + 1
                            if json_start >= 0 and json_end > json_start:
                                json_content = content[json_start:json_end]
                                parsed_data = json.loads(json_content)

                                articles = parsed_data.get('articles', [])
                                logger.info(f"Perplexity found {len(articles)} articles")
                                return {
                                    'articles': articles,
                                    'source': 'perplexity',
                                    'total_found': len(articles)
                                }
                        except json.JSONDecodeError:
                            logger.warning("Failed to parse JSON from Perplexity response")

                    else:
                        logger.warning(f"Perplexity API returned {response.status}")

        except Exception as e:
            logger.warning(f"Perplexity news search failed: {e}")

        return {'articles': [], 'source': 'perplexity', 'total_found': 0}

    async def _search_perplexity_synthesis(self, query: str, max_results: int) -> Dict[str, Any]:
        """Use Perplexity chat/completion API to produce a synthesized answer with citations.

        Returns a dict with keys:
        - synthesis: string answer
        - citations: list of {title, url, snippet, source}
        """
        logger.info(f"Starting Perplexity synthesis search for: '{query}'")

        try:
            url = "https://api.perplexity.ai/chat/completions"
            headers = {
                'Authorization': f'Bearer {self.perplexity_api_key}',
                'Content-Type': 'application/json'
            }

            # Prompt the model to provide a concise synthesized answer with citations
            prompt = f"""Provide a concise, factual answer to the user query below. After the answer,
provide a JSON object with an `answer` string and a `citations` array. Each citation should have: title, url, snippet, and source.

Query: {query}

Return only valid JSON in the following exact format:
{{
  "answer": "...",
  "citations": [
    {{"title": "...", "url": "https://...", "snippet": "...", "source": "..."}}
  ]
}}
"""

            data = {
                'model': os.getenv('PERPLEXITY_MODEL', 'sonar-pro'),
                'messages': [
                    {
                        'role': 'system',
                        'content': "You are a helpful research assistant. Provide concise factual answers and include citations in JSON format."
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'max_tokens': 1600
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result['choices'][0]['message']['content']

                        # Extract JSON block from the response
                        try:
                            json_start = content.find('{')
                            json_end = content.rfind('}') + 1
                            if json_start >= 0 and json_end > json_start:
                                json_content = content[json_start:json_end]
                                parsed = json.loads(json_content)
                                answer = parsed.get('answer', '')
                                citations = parsed.get('citations', [])

                                # Normalize citations
                                normalized = []
                                for c in citations[:max_results]:
                                    normalized.append({
                                        'title': c.get('title') if isinstance(c, dict) else str(c),
                                        'url': c.get('url') if isinstance(c, dict) else None,
                                        'snippet': c.get('snippet') if isinstance(c, dict) else None,
                                        'source': c.get('source') if isinstance(c, dict) else None
                                    })

                                return {
                                    'synthesis': answer,
                                    'citations': normalized,
                                    'source': 'perplexity',
                                    'total_found': len(normalized)
                                }
                        except Exception:
                            logger.warning('Failed to parse JSON from Perplexity synthesis response')
                    else:
                        logger.warning(f'Perplexity synthesis API returned {response.status}')

        except Exception as e:
            logger.warning(f'Perplexity synthesis search failed: {e}')

        return {'synthesis': '', 'citations': [], 'source': 'perplexity', 'total_found': 0}

    def _filter_and_deduplicate_articles(self, articles: List[Dict[str, Any]], max_results: int) -> List[Dict[str, Any]]:
        """Filter and deduplicate articles."""
        seen_urls = set()
        filtered_articles = []

        for article in articles:
            url = article.get('url', '').strip()
            title = article.get('title', '').strip()

            # Skip if URL already seen or empty
            if not url or url in seen_urls:
                continue

            # Skip if title is too short or generic
            if len(title) < 10 or title.lower().startswith('[removed]'):
                continue

            seen_urls.add(url)
            filtered_articles.append(article)

            if len(filtered_articles) >= max_results * 2:  # Get more than needed for better sorting
                break

        return filtered_articles

    def _deduplicate_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate articles based on URL."""
        seen_urls = set()
        deduplicated = []

        for article in articles:
            url = article.get('url', '').strip()
            if url and url not in seen_urls:
                seen_urls.add(url)
                deduplicated.append(article)

        return deduplicated

    def _sort_articles(self, articles: List[Dict[str, Any]], sort_by: str) -> List[Dict[str, Any]]:
        """Sort articles based on sort_by parameter."""
        if sort_by == "date":
            return sorted(articles, key=lambda x: x.get('published_at', ''), reverse=True)
        elif sort_by == "popularity":
            # For now, sort by date as proxy for popularity
            return sorted(articles, key=lambda x: x.get('published_at', ''), reverse=True)
        else:  # relevance (default)
            # Sort by date first, then by source credibility
            source_priority = {
                'Reuters': 10, 'BBC News': 9, 'Associated Press': 8, 'CNN': 7,
                'New York Times': 6, 'Washington Post': 5, 'Bloomberg': 4,
                'Wall Street Journal': 3, 'NPR': 2
            }

            def sort_key(article):
                date_score = article.get('published_at', '')
                source_score = source_priority.get(article.get('source', ''), 0)
                return (source_score, date_score)

            return sorted(articles, key=sort_key, reverse=True)

    async def _search_google_news_basic(self, topic: str, max_results: int) -> Dict[str, Any]:
        """Enhanced Google Search for recent news articles with better targeting."""
        logger.info(f"Starting enhanced Google Search for: {topic}")
        
        # Calculate date range for recent news (last 14 days for better coverage)
        date_restrict = "d14"
        
        # Enhanced search queries - try multiple approaches
        search_queries = [
            f"{topic} news latest",
            f'"{topic}" breaking news',
            f"{topic} recent developments",
            f"{topic} today news"
        ]
        
        all_articles = []
        
        for query in search_queries[:2]:  # Try top 2 queries to avoid rate limits
            try:
                url = "https://www.googleapis.com/customsearch/v1"
                params = {
                    'key': self.google_api_key,
                    'cx': self.google_search_engine_id,
                    'q': query,
                    'num': min(5, max_results),  # Fewer per query, more targeted
                    'dateRestrict': date_restrict,
                    'sort': 'date',
                    # Enhanced site search for major news sources
                    'siteSearch': ('news.google.com OR reuters.com OR bbc.com OR cnn.com OR '
                                 'apnews.com OR npr.org OR nbcnews.com OR abcnews.go.com OR '
                                 'cbsnews.com OR foxnews.com OR bloomberg.com OR wsj.com OR '
                                 'nytimes.com OR washingtonpost.com'),
                    'lr': 'lang_en',
                    'tbm': 'nws'  # News search
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            for item in data.get('items', []):
                                # Enhanced article parsing
                                article = {
                                    'title': item.get('title', '').replace(' - ', ' | '),
                                    'snippet': item.get('snippet', ''),
                                    'link': item.get('link', ''),
                                    'source': item.get('displayLink', '').replace('www.', ''),
                                    'date': self._extract_date_from_item(item),
                                    'search_query': query,
                                    'provider': 'google_search'
                                }
                                
                                # Filter out duplicates and low-quality results
                                if (article['title'] and article['snippet'] and 
                                    len(article['snippet']) > 50 and
                                    not any(existing['link'] == article['link'] for existing in all_articles)):
                                    all_articles.append(article)
                                    
                        else:
                            logger.warning(f"Google Search API returned {response.status} for query: {query}")
                            
            except Exception as e:
                logger.warning(f"Google Search query '{query}' failed: {e}")
                continue
        
        # Sort by date and limit results
        all_articles = sorted(all_articles, key=lambda x: x.get('date', ''), reverse=True)[:max_results]
        
        summary = self._generate_summary_from_articles(all_articles, topic) if all_articles else ""
        
        return {
            'articles': all_articles,
            'summary': summary,
            'source': 'google_search',
            'queries_used': search_queries[:2],
            'total_found': len(all_articles)
        }
    
    async def _search_perplexity_enhanced(self, topic: str) -> Dict[str, Any]:
        """Enhanced Perplexity search using search-enabled models for comprehensive research."""
        logger.info(f"Starting enhanced Perplexity research for: {topic}")
        
        # Get current date/time context
        current_context = get_current_context()
        
        # Try search-enabled models in order of preference
        for model in self.perplexity_search_models:
            try:
                url = "https://api.perplexity.ai/chat/completions"
                
                # Enhanced research prompt for comprehensive analysis
                research_prompt = f"""Conduct comprehensive research on "{topic}". 

{current_context}

Please provide:

1. **Current Status & Latest Developments**: What's happening with {topic} right now TODAY and THIS WEEK? Include specific recent events, dates from 2025, and developments from the past 2 weeks.

2. **Key Facts & Background**: Essential information about {topic} - what it is, key players/organizations involved, and important context.

3. **Recent News & Updates**: Summarize the most important news from January 2025 and late 2024 about this topic.

4. **Multiple Perspectives**: Present different viewpoints or aspects of this topic if relevant.

5. **Sources & References**: Include specific sources, dates, and credible references where possible. Use 2025 dates if available.

IMPORTANT: Focus ONLY on information from 2024-2025. Do not provide information from 2021, 2022, or 2023 unless asked for historical context.
Provide factual, up-to-date information with specific details and dates from the current year."""
                
                headers = {
                    'Authorization': f'Bearer {self.perplexity_api_key}',
                    'Content-Type': 'application/json'
                }
                
                payload = {
                    'model': model,
                    'messages': [
                        {
                            'role': 'system',
                            'content': f"""You are a professional researcher and journalist specializing in current events and news.
{current_context}

Important guidelines:
- Today's date is in 2025
- Focus ONLY on recent developments from 2024-2025
- Never provide outdated information from 2021, 2022, or 2023
- Always include specific dates and sources
- Provide the most current information available
- If you're uncertain about dates, verify they are recent

{get_current_context()}"""
                        },
                        {
                            'role': 'user',
                            'content': research_prompt
                        }
                    ],
                    'max_tokens': 2000,  # Increased for comprehensive research
                    'temperature': 0.1,
                    'stream': False,
                    'search_domain_filter': ["news.google.com", "reuters.com", "bbc.com", "cnn.com", "apnews.com", "npr.org"]
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, json=payload) as response:
                        if response.status == 200:
                            data = await response.json()
                            content = data['choices'][0]['message']['content']
                            
                            # Extract search results if available (Perplexity provides these)
                            search_results = data.get('search_results', [])
                            articles = []
                            
                            # Create articles from search results if available
                            if search_results:
                                for result in search_results[:5]:  # Use top 5 search results
                                    article = {
                                        'title': result.get('title', ''),
                                        'snippet': content[:200] + "..." if len(content) > 200 else content,
                                        'content': content,
                                        'link': result.get('url', ''),
                                        'source': self._extract_domain_from_url(result.get('url', '')),
                                        'date': result.get('date', datetime.now().strftime('%Y-%m-%d')),
                                        'provider': 'perplexity',
                                        'search_result': True
                                    }
                                    if article['title'] and article['link']:
                                        articles.append(article)
                            
                            # Always include the comprehensive analysis as the main article
                            comprehensive_article = {
                                'title': f"Comprehensive Research: {topic}",
                                'snippet': content[:300] + "..." if len(content) > 300 else content,
                                'content': content,
                                'source': f'perplexity.ai ({model})',
                                'date': datetime.now().strftime('%Y-%m-%d'),
                                'provider': 'perplexity',
                                'model_used': model,
                                'research_type': 'comprehensive_analysis',
                                'link': f'https://perplexity.ai/search?q={topic.replace(" ", "+")}'
                            }
                            articles.insert(0, comprehensive_article)  # Put comprehensive analysis first
                            
                            # Extract citations/sources if mentioned in the content
                            sources = self._extract_sources_from_content(content)
                            if sources:
                                comprehensive_article['cited_sources'] = sources
                            
                            logger.info(f"Perplexity research successful with model: {model}, {len(search_results)} search results")
                            return {
                                'articles': articles,
                                'summary': content,
                                'source': 'perplexity',
                                'model_used': model,
                                'search_results_count': len(search_results),
                                'research_comprehensive': True
                            }
                            
                        elif response.status == 429:
                            logger.warning(f"Rate limit hit for model {model}, trying next model...")
                            continue
                        else:
                            error_text = await response.text()
                            logger.warning(f"Perplexity API error {response.status} for model {model}: {error_text}")
                            continue
                            
            except Exception as e:
                logger.warning(f"Perplexity model {model} failed: {e}")
                continue
        
        raise Exception("All Perplexity models failed or rate limited")
    
    async def _search_newsapi(self, topic: str, max_results: int) -> Dict[str, Any]:
        """Search NewsAPI for current news articles."""
        logger.info(f"Starting NewsAPI search for: {topic}")
        
        try:
            # Calculate date range for recent news (last 7 days)
            from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            
            url = "https://newsapi.org/v2/everything"
            params = {
                'apiKey': self.news_api_key,
                'q': topic,
                'from': from_date,
                'sortBy': 'publishedAt',
                'pageSize': min(max_results, 20),  # NewsAPI allows up to 20
                'language': 'en',
                'domains': 'reuters.com,bbc.com,cnn.com,apnews.com,npr.org,nbcnews.com,abcnews.go.com,cbsnews.com,bloomberg.com'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        articles = []
                        for article in data.get('articles', []):
                            # Skip articles without proper content
                            if not article.get('title') or not article.get('description'):
                                continue
                            
                            news_article = {
                                'title': article['title'],
                                'snippet': article.get('description', ''),
                                'content': article.get('content', article.get('description', '')),
                                'link': article.get('url', ''),
                                'source': article.get('source', {}).get('name', 'NewsAPI'),
                                'date': article.get('publishedAt', '')[:10] if article.get('publishedAt') else datetime.now().strftime('%Y-%m-%d'),
                                'author': article.get('author', ''),
                                'provider': 'newsapi'
                            }
                            
                            # Filter out removed/deleted articles
                            if '[Removed]' not in news_article['title'] and news_article['snippet']:
                                articles.append(news_article)
                        
                        # Sort by date
                        articles = sorted(articles, key=lambda x: x.get('date', ''), reverse=True)
                        
                        summary = self._generate_summary_from_articles(articles, topic) if articles else ""
                        
                        logger.info(f"NewsAPI found {len(articles)} articles")
                        return {
                            'articles': articles,
                            'summary': summary,
                            'source': 'newsapi',
                            'total_found': len(articles)
                        }
                        
                    else:
                        error_text = await response.text()
                        logger.warning(f"NewsAPI returned {response.status}: {error_text}")
                        raise Exception(f"NewsAPI error {response.status}: {error_text}")
                        
        except Exception as e:
            logger.warning(f"NewsAPI search failed: {e}")
            raise
    
    def _generate_summary_from_articles(self, articles: List[Dict], topic: str) -> str:
        """Generate a comprehensive summary from multiple articles."""
        if not articles:
            return f"Recent developments about {topic}"
        
        # Enhanced summary generation
        summary_parts = []
        unique_sources = set()
        
        for article in articles[:5]:  # Use top 5 articles
            snippet = article.get('snippet', '')
            content = article.get('content', '')
            source = article.get('source', 'Unknown')
            
            # Use content if available, otherwise snippet
            text = content if content and len(content) > len(snippet) else snippet
            
            if text and len(text.strip()) > 30:
                # Clean up text
                clean_text = text.replace('...', '').replace('\n', ' ').strip()
                if clean_text and clean_text not in summary_parts:
                    summary_parts.append(clean_text)
                    unique_sources.add(source)
        
        if summary_parts:
            # Combine summaries with source attribution
            combined_summary = ' | '.join(summary_parts[:3])  # Top 3 summaries
            source_list = ', '.join(list(unique_sources)[:3])
            return f"{combined_summary}\n\nSources: {source_list}"
        else:
            return f"Latest news and updates about {topic}"
    
    async def _generate_comprehensive_summary(self, articles: List[Dict], topic: str, 
                                            google_results: Optional[Dict] = None, 
                                            perplexity_results: Optional[Dict] = None,
                                            newsapi_results: Optional[Dict] = None) -> str:
        """Generate a comprehensive summary combining all research sources."""
        summary_parts = []
        
        # Add Perplexity comprehensive analysis first (if available)
        if perplexity_results and perplexity_results.get('summary'):
            perplexity_summary = perplexity_results['summary']
            if len(perplexity_summary) > 100:  # Substantial content
                summary_parts.append(f"**Comprehensive Analysis:**\n{perplexity_summary}")
        
        # Add news summaries from different sources
        news_sources = []
        if google_results and google_results.get('articles'):
            google_summary = self._generate_summary_from_articles(google_results['articles'], topic)
            if google_summary and "Recent developments" not in google_summary:
                news_sources.append(f"Google Search: {google_summary}")
        
        if newsapi_results and newsapi_results.get('articles'):
            newsapi_summary = self._generate_summary_from_articles(newsapi_results['articles'], topic)
            if newsapi_summary and "Recent developments" not in newsapi_summary:
                news_sources.append(f"NewsAPI: {newsapi_summary}")
        
        if news_sources:
            summary_parts.append(f"**Latest News:**\n" + "\n\n".join(news_sources))
        
        # Add article count summary
        if articles:
            source_counts = {}
            for article in articles:
                provider = article.get('provider', 'unknown')
                source_counts[provider] = source_counts.get(provider, 0) + 1
            
            count_summary = ", ".join([f"{count} from {provider}" for provider, count in source_counts.items()])
            summary_parts.append(f"**Sources:** {len(articles)} articles total ({count_summary})")
        
        # Combine all summaries
        if summary_parts:
            return "\n\n".join(summary_parts)
        else:
            return f"Comprehensive research on {topic} - Recent developments and analysis from multiple sources."
    
    def _extract_date_from_item(self, item: Dict) -> str:
        """Extract and format date from Google Search item."""
        # Try multiple date fields
        date_fields = ['htmlFormattedUrl', 'formattedUrl', 'snippet']
        
        for field in date_fields:
            if field in item:
                text = item[field]
                # Look for date patterns in the text
                import re
                date_patterns = [
                    r'\d{1,2}/\d{1,2}/\d{4}',  # MM/DD/YYYY
                    r'\d{4}-\d{2}-\d{2}',      # YYYY-MM-DD
                    r'\w+ \d{1,2}, \d{4}'      # Month DD, YYYY
                ]
                
                for pattern in date_patterns:
                    match = re.search(pattern, text)
                    if match:
                        return match.group()
        
        # Fallback to current date
        return datetime.now().strftime('%Y-%m-%d')
    
    def _extract_sources_from_content(self, content: str) -> List[str]:
        """Extract source references from Perplexity content."""
        import re
        sources = []
        
        # Look for URL patterns
        url_pattern = r'https?://[^\s<>"{}|\\^`[\]]+'
        urls = re.findall(url_pattern, content)
        
        # Look for source mentions
        source_patterns = [
            r'according to ([^,\n]+)',
            r'reports ([^,\n]+)',
            r'source: ([^,\n]+)',
            r'via ([^,\n]+)'
        ]
        
        for pattern in source_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            sources.extend(matches)
        
        # Clean and deduplicate
        clean_sources = []
        for source in (urls + sources):
            clean_source = source.strip().rstrip('.,;')
            if clean_source and len(clean_source) > 3 and clean_source not in clean_sources:
                clean_sources.append(clean_source)
        
        return clean_sources[:10]  # Limit to 10 sources
    
    def _extract_domain_from_url(self, url: str) -> str:
        """Extract domain name from URL for display."""
        if not url:
            return 'Unknown'
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain or 'Unknown'
        except Exception:
            return 'Unknown'
    
    def _generate_fallback_response(self, topic: str) -> Dict[str, Any]:
        """Generate a helpful fallback response when no APIs work."""
        return {
            'articles': [{
                'title': f"Research Topic: {topic}",
                'snippet': f"Unable to fetch current news about {topic} due to API limitations. Please try again later or check news sources directly.",
                'content': f"This topic requires real-time news research. Our news research APIs are currently unavailable, but you can find current information about '{topic}' by visiting major news websites like BBC, CNN, Reuters, or Google News.",
                'source': 'system_fallback',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'provider': 'fallback'
            }],
            'summary': f"News research for '{topic}' is currently unavailable. Please check major news sources or try again later.",
            'sources_used': ['fallback'],
            'total_sources': 0,
            'research_date': datetime.now().isoformat(),
            'query_used': topic
        }
    
    def _generate_error_response(self, topic: str, error_message: str) -> Dict[str, Any]:
        """Generate an error response with helpful information."""
        return {
            'articles': [{
                'title': f"Research Error: {topic}",
                'snippet': f"An error occurred while researching {topic}: {error_message}",
                'content': f"We encountered an issue while researching '{topic}'. Error: {error_message}. Please try again or contact support if the issue persists.",
                'source': 'system_error',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'provider': 'error'
            }],
            'summary': f"Unable to complete research for '{topic}' due to an error: {error_message}",
            'sources_used': ['error'],
            'total_sources': 0,
            'research_date': datetime.now().isoformat(),
            'query_used': topic,
            'error': error_message
        }
    
    def get_news_keywords(self, topic: str) -> List[str]:
        """Generate keywords for news-related video search."""
        base_keywords = [
            "breaking news", "news report", "journalism", "news anchor",
            "newsroom", "headlines", "current events", "media coverage",
            "press conference", "news bulletin", "live news"
        ]
        
        # Add topic-specific keywords
        topic_words = topic.lower().split()
        extended_keywords = base_keywords + topic_words
        
        return extended_keywords


# Singleton instance
news_research_service = NewsResearchService()