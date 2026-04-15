"""
Postiz API service for scheduling social media posts.
"""
import os
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
import aiohttp
from loguru import logger
from pydantic import BaseModel, Field


class PostizIntegration(BaseModel):
    """Postiz integration model."""
    id: str
    name: str
    provider: str


class PostizImageAttachment(BaseModel):
    """Postiz image attachment model."""
    id: str
    path: str


class PostizPostValue(BaseModel):
    """Postiz post value model."""
    content: str
    image: Optional[List[PostizImageAttachment]] = None


class PostizTag(BaseModel):
    """Postiz tag model."""
    value: str
    label: str


class PostizPost(BaseModel):
    """Postiz post model."""
    integration: PostizIntegration
    value: List[PostizPostValue]
    settings: Optional[Dict[str, Any]] = None


class PostizCreatePostRequest(BaseModel):
    """Postiz create post request model."""
    type: str = Field(..., description="Post type: draft, schedule, or now")
    date: str = Field(..., description="ISO 8601 datetime for posts")
    shortLink: bool = Field(..., description="Whether to create short links (required)")
    posts: List[PostizPost]
    tags: Optional[List[PostizTag]] = None


class PostizUploadResponse(BaseModel):
    """Postiz upload response model."""
    id: str
    path: str


class PostizService:
    """Service for interacting with Postiz API."""
    
    def __init__(self):
        """Initialize Postiz service."""
        self.api_key = os.getenv("POSTIZ_API_KEY")
        self.api_url = os.getenv("POSTIZ_API_URL", "https://api.postiz.com/public/v1")
        
        if not self.api_key:
            logger.warning("POSTIZ_API_KEY not found in environment variables")
        else:
            # Log first/last 4 chars of API key for debugging (keep middle hidden)
            masked_key = f"{self.api_key[:4]}...{self.api_key[-4:]}" if len(self.api_key) > 8 else "***"
            logger.info(f"POSTIZ_API_KEY found: {masked_key}")
        
        self.headers = {
            "Authorization": f"{self.api_key}",  # No "Bearer " prefix for this instance
            "Content-Type": "application/json"
        }
        
        logger.info(f"Initialized Postiz service with API URL: {self.api_url}")
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, files: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to Postiz API."""
        if not self.api_key:
            raise ValueError("Postiz API key not configured")
        
        url = f"{self.api_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        async with aiohttp.ClientSession() as session:
            headers = self.headers.copy()
            
            # Remove Content-Type for file uploads
            if files:
                headers.pop("Content-Type", None)
            
            try:
                async with session.request(
                    method=method,
                    url=url,
                    json=data if not files else None,
                    data=files if files else None,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response_data = await response.json()
                    
                    if response.status >= 400:
                        logger.error(f"Postiz API error {response.status}: {response_data}")
                        raise Exception(f"Postiz API error: {response_data.get('message', 'Unknown error')}")
                    
                    return response_data
                    
            except asyncio.TimeoutError:
                logger.error(f"Timeout making {method} request to {url}")
                raise Exception("Request to Postiz API timed out")
            except Exception as e:
                logger.error(f"Error making {method} request to {url}: {e}")
                raise
    
    async def get_integrations(self) -> List[PostizIntegration]:
        """Get available social media integrations."""
        try:
            response = await self._make_request("GET", "/integrations")
            integrations: List[PostizIntegration] = []
            
            # Handle both list and dict response formats
            integration_list: List[Dict[str, Any]]
            if isinstance(response, list):
                # Direct list response (self-hosted Postiz)
                integration_list = response
            else:
                # Dict response with "data" field (cloud Postiz)
                integration_list = response.get("data", [])
            
            for integration_data in integration_list:
                # Ensure integration_data is treated as a dictionary
                if isinstance(integration_data, dict):
                    integration = PostizIntegration(
                        id=integration_data["id"],
                        name=integration_data.get("name", ""),
                        provider=integration_data.get("identifier", integration_data.get("provider", ""))  # Use identifier field for provider
                    )
                    integrations.append(integration)
            
            logger.info(f"Retrieved {len(integrations)} Postiz integrations")
            return integrations
            
        except Exception as e:
            logger.error(f"Failed to get Postiz integrations: {e}")
            raise
    
    async def upload_media(self, file_path: str, file_name: Optional[str] = None) -> PostizUploadResponse:
        """Upload media file to Postiz."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not file_name:
            file_name = os.path.basename(file_path)
        
        try:
            # Create form data for file upload
            data = aiohttp.FormData()
            data.add_field('file', 
                          open(file_path, 'rb'),
                          filename=file_name,
                          content_type='application/octet-stream')
            
            # Use the aiohttp FormData directly
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"{self.api_key}"}
                url = f"{self.api_url.rstrip('/')}/upload"
                
                async with session.post(url, data=data, headers=headers) as response:
                    response_data = await response.json()
                    
                    if response.status >= 400:
                        logger.error(f"Postiz upload error {response.status}: {response_data}")
                        raise Exception(f"Upload failed: {response_data.get('message', 'Unknown error')}")
                    
                    upload_response = PostizUploadResponse(
                        id=response_data["id"],
                        path=response_data["path"]
                    )
                    
                    logger.info(f"Successfully uploaded {file_name} to Postiz (ID: {upload_response.id})")
                    return upload_response
                    
        except Exception as e:
            logger.error(f"Failed to upload {file_path} to Postiz: {e}")
            raise
    
    async def create_post(self, post_request: PostizCreatePostRequest) -> Dict[str, Any]:
        """Create/schedule a post on Postiz."""
        try:
            request_data = post_request.model_dump(exclude_none=True)
            logger.info(f"Sending Postiz post request: {request_data}")
            response = await self._make_request("POST", "/posts", data=request_data)
            
            # Handle both dict and list responses from Postiz API
            if isinstance(response, list):
                # When API returns a list, it's usually a success response with post IDs
                logger.info(f"Successfully created Postiz post (response list length: {len(response)})")
                return {"success": True, "posts": response}
            else:
                # Normal dict response
                logger.info(f"Successfully created Postiz post (ID: {response.get('id', 'unknown')})")
                return response
            
        except Exception as e:
            logger.error(f"Failed to create Postiz post: {e}")
            raise
    
    async def schedule_post_now(self, content: str, integrations: List[str], media_paths: Optional[List[str]] = None, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Schedule a post to be published immediately."""
        return await self.schedule_post(
            content=content,
            integrations=integrations,
            post_type="now",
            schedule_date=None,
            media_paths=media_paths,
            tags=tags
        )
    
    async def schedule_post_later(self, content: str, integrations: List[str], schedule_date: datetime, media_paths: Optional[List[str]] = None, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Schedule a post for a specific date and time."""
        return await self.schedule_post(
            content=content,
            integrations=integrations,
            post_type="schedule",
            schedule_date=schedule_date,
            media_paths=media_paths,
            tags=tags
        )
    
    async def create_draft_post(self, content: str, integrations: List[str], media_paths: Optional[List[str]] = None, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a draft post."""
        return await self.schedule_post(
            content=content,
            integrations=integrations,
            post_type="draft",
            schedule_date=None,
            media_paths=media_paths,
            tags=tags
        )
    
    async def schedule_post(self, content: str, integrations: List[str], post_type: str = "now", schedule_date: Optional[datetime] = None, media_paths: Optional[List[str]] = None, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Schedule a post with the given parameters.
        
        Args:
            content: Post content text
            integrations: List of integration IDs to post to
            post_type: Type of post - "now", "schedule", or "draft"
            schedule_date: DateTime for scheduled posts (required if post_type is "schedule")
            media_paths: Optional list of local file paths to upload and attach
            tags: Optional list of tags
            
        Returns:
            Postiz API response
        """
        if not content.strip():
            raise ValueError("Post content cannot be empty")
        
        if not integrations:
            raise ValueError("At least one integration must be specified")
        
        if post_type == "schedule" and not schedule_date:
            raise ValueError("Schedule date is required for scheduled posts")
        
        try:
            # Upload media files if provided
            uploaded_images = []
            if media_paths:
                logger.info(f"Processing {len(media_paths)} media files for upload to Postiz")
                for media_path in media_paths:
                    logger.info(f"Processing media path: {media_path}")
                    if media_path.startswith('http://') or media_path.startswith('https://'):
                        # Download from URL and upload
                        try:
                            logger.info(f"Downloading and uploading media from URL: {media_path}")
                            upload_response = await self.download_and_upload_media(media_path)
                            uploaded_images.append(PostizImageAttachment(
                                id=upload_response.id,
                                path=upload_response.path
                            ))
                            logger.info(f"Successfully uploaded media to Postiz (ID: {upload_response.id}, Path: {upload_response.path})")
                        except Exception as e:
                            logger.error(f"Failed to download and upload media from {media_path}: {e}")
                            raise  # Re-raise to ensure the error is not silently ignored
                    elif os.path.exists(media_path):
                        # Upload local file
                        upload_response = await self.upload_media(media_path)
                        uploaded_images.append(PostizImageAttachment(
                            id=upload_response.id,
                            path=upload_response.path
                        ))
                    else:
                        logger.warning(f"Media file not found or invalid URL: {media_path}")
                        logger.debug(f"URL analysis: starts_with_http={media_path.startswith('http') if media_path else False}, "
                                    f"starts_with_https={media_path.startswith('https') if media_path else False}, "
                                    f"is_local_file={os.path.exists(media_path) if media_path else False}")
            
            # Get available integrations to validate IDs
            available_integrations = await self.get_integrations()
            integration_map = {integration.id: integration for integration in available_integrations}
            
            # Build posts for each integration
            posts = []
            for integration_id in integrations:
                if integration_id not in integration_map:
                    logger.warning(f"Integration ID {integration_id} not found in available integrations")
                    continue
                
                integration = integration_map[integration_id]
                post_value = PostizPostValue(
                    content=content,
                    image=uploaded_images if uploaded_images else []
                )
                
                # Add provider-specific settings
                post_settings = None
                if integration.provider == "youtube":
                    # YouTube requires title and type settings
                    post_settings = {
                        "title": content[:100] if len(content) <= 100 else content[:97] + "...",  # YouTube title limit
                        "type": "public"  # Default to public
                    }
                elif integration.provider == "instagram":
                    # Instagram requires post_type setting
                    post_settings = {
                        "post_type": "post"  # Default to post (not story)
                    }
                
                post = PostizPost(
                    integration=integration,
                    value=[post_value],
                    settings=post_settings
                )
                posts.append(post)
            
            if not posts:
                raise ValueError("No valid integrations found")
            
            # Convert tags to PostizTag objects (always ensure an array, even if empty)
            postiz_tags = []
            if tags:
                postiz_tags = [PostizTag(value=tag, label=tag) for tag in tags]
            
            # Ensure we always have a date (use current time for immediate posts)
            post_date = schedule_date.isoformat() if schedule_date else datetime.now().isoformat()
            
            # Create the post request
            post_request = PostizCreatePostRequest(
                type=post_type,
                date=post_date,
                shortLink=False,
                posts=posts,
                tags=postiz_tags
            )
            
            return await self.create_post(post_request)
            
        except Exception as e:
            logger.error(f"Failed to schedule post: {e}")
            raise
    
    async def download_and_upload_media(self, media_url: str, filename: Optional[str] = None) -> PostizUploadResponse:
        """Download media from URL and upload to Postiz."""
        import tempfile
        from urllib.parse import urlparse
        
        try:
            # Determine file extension from URL if filename not provided
            if not filename:
                parsed_url = urlparse(media_url)
                path_parts = parsed_url.path.split('/')
                if path_parts and '.' in path_parts[-1]:
                    filename = path_parts[-1]
                else:
                    # Default based on content type or assume common format
                    filename = "media.jpg"  # Will be updated based on response headers
            
            # Download the media file
            async with aiohttp.ClientSession() as session:
                async with session.get(media_url) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to download media: HTTP {response.status}")
                    
                    # Try to get filename from Content-Disposition or Content-Type
                    content_type = response.headers.get('content-type', '').lower()
                    if not filename or filename == "media.jpg":
                        if 'video' in content_type:
                            filename = "video.mp4"
                        elif 'audio' in content_type:
                            filename = "audio.mp3"
                        elif 'image/png' in content_type:
                            filename = "image.png"
                        elif 'image' in content_type:
                            filename = "image.jpg"
                    
                    # Create a temporary file
                    suffix = os.path.splitext(filename)[1] or '.tmp'
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                        temp_path = temp_file.name
                        
                        # Write media content to temp file
                        async for chunk in response.content.iter_chunked(8192):
                            temp_file.write(chunk)
            
            # Upload to Postiz
            try:
                upload_response = await self.upload_media(temp_path, filename)
                logger.info(f"Successfully uploaded media to Postiz: {upload_response.id}")
                return upload_response
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_path)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Failed to download and upload media: {e}")
            raise

    async def download_and_upload_video(self, video_url: str) -> PostizUploadResponse:
        """Download video from URL and upload to Postiz."""
        return await self.download_and_upload_media(video_url, "video.mp4")

    async def schedule_video_post(self, video_url: str, content: str, integrations: List[str], post_type: str = "now", schedule_date: Optional[datetime] = None, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Schedule a post with video content by downloading and uploading the video.
        
        Args:
            video_url: URL of the video to post
            content: Post content text
            integrations: List of integration IDs to post to
            post_type: Type of post - "now", "schedule", or "draft"
            schedule_date: DateTime for scheduled posts
            tags: Optional list of tags
            
        Returns:
            Postiz API response
        """
        try:
            # Download and upload the video to Postiz
            video_upload = await self.download_and_upload_video(video_url)
            
            # Get available integrations to validate IDs
            available_integrations = await self.get_integrations()
            integration_map = {integration.id: integration for integration in available_integrations}
            
            # Build posts for each integration with video attachment
            posts = []
            for integration_id in integrations:
                if integration_id not in integration_map:
                    logger.warning(f"Integration ID {integration_id} not found in available integrations")
                    continue
                
                integration = integration_map[integration_id]
                
                # Create video attachment (treat as image for now - Postiz API compatibility)
                video_attachment = PostizImageAttachment(
                    id=video_upload.id,
                    path=video_upload.path
                )
                
                post_value = PostizPostValue(
                    content=content,
                    image=[video_attachment]  # Postiz uses 'image' field for all media
                )
                
                # Add provider-specific settings
                post_settings = None
                if integration.provider == "youtube":
                    # YouTube requires title and type settings
                    post_settings = {
                        "title": content[:100] if len(content) <= 100 else content[:97] + "...",  # YouTube title limit
                        "type": "public"  # Default to public
                    }
                elif integration.provider == "instagram":
                    # Instagram requires post_type setting
                    post_settings = {
                        "post_type": "post"  # Default to post (not story)
                    }
                
                post = PostizPost(
                    integration=integration,
                    value=[post_value],
                    settings=post_settings
                )
                posts.append(post)
            
            if not posts:
                raise ValueError("No valid integrations found")
            
            # Convert tags to PostizTag objects (always ensure an array, even if empty)
            postiz_tags = []
            if tags:
                postiz_tags = [PostizTag(value=tag, label=tag) for tag in tags]
            
            # Ensure we always have a date (use current time for immediate posts)
            post_date = schedule_date.isoformat() if schedule_date else datetime.now().isoformat()
            
            # Create the post request
            post_request = PostizCreatePostRequest(
                type=post_type,
                date=post_date,
                shortLink=False,
                posts=posts,
                tags=postiz_tags
            )
            
            return await self.create_post(post_request)
            
        except Exception as e:
            logger.error(f"Failed to schedule video post: {e}")
            raise

    def add_to_post_history(self, post_data: dict) -> None:
        """Add a post to the history storage."""
        from datetime import datetime

        history_entry = {
            "id": f"post_{len(_post_history) + 1}_{int(datetime.now().timestamp())}",
            "content": post_data.get("content", ""),
            "integrations": post_data.get("integrations", []),
            "post_type": post_data.get("post_type", "now"),
            "status": "published" if post_data.get("post_type") == "now" else post_data.get("post_type", "draft"),
            "created_at": datetime.now().isoformat(),
            "media_urls": post_data.get("media_urls", []),
            "tags": post_data.get("tags", []),
            "post_id": post_data.get("response_data", {}).get("data", {}).get("posts", [{}])[0].get("postId")
        }

        _post_history.insert(0, history_entry)  # Add to beginning (newest first)

        # Keep only last 100 posts in memory
        if len(_post_history) > 100:
            _post_history.pop()

    def get_post_history(self) -> list[dict]:
        """Get the post history."""
        return _post_history.copy()

# Simple in-memory post history storage
_post_history: list[dict] = []

# Lazy singleton initialization
_postiz_service_instance = None

def get_postiz_service() -> PostizService:
    """Get or create the singleton PostizService instance."""
    global _postiz_service_instance
    if _postiz_service_instance is None:
        _postiz_service_instance = PostizService()
    return _postiz_service_instance

# For backward compatibility
postiz_service = get_postiz_service()