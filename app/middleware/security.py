"""
Enhanced security middleware for handling common attack patterns, rate limiting, and IP blocking.
"""
import logging
import time
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Dict, Set
import re
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Enhanced security middleware with advanced threat detection and IP blocking"""
    
    # Common attack patterns to detect and log
    SUSPICIOUS_PATTERNS = [
        r'\.sql$',
        r'\.tar\.gz$',
        r'\.zip$',
        r'\.bak$',
        r'\.backup$',
        r'database',
        r'backup',
        r'admin\.php',
        r'wp-admin',
        r'phpmyadmin',
        r'\.env$',
        r'config\.php',
        r'\.git/',
        r'\.svn/',
        r'/etc/passwd',
        r'/proc/',
        r'\.\./',  # Directory traversal
        r'<script',  # XSS attempts
        r'union.*select',  # SQL injection
        r'drop.*table',  # SQL injection
        r'shell_exec',  # Code injection
        r'eval\(',  # Code injection
        r'base64_decode',  # Malicious payloads
        r'\.\.\\',  # Windows directory traversal
        r'cmd\.exe',  # Windows command injection
        r'/bin/sh',  # Unix shell injection
    ]
    
    # Compile patterns for better performance
    COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in SUSPICIOUS_PATTERNS]
    
    def __init__(self, app, log_all_404s: bool = True):
        super().__init__(app)
        self.log_all_404s = log_all_404s
        
        # Enhanced tracking systems
        self.request_count = defaultdict(deque)  # IP -> deque of request timestamps
        self.suspicious_count = defaultdict(int)  # IP -> suspicious request count
        self.blocked_ips: Set[str] = set()  # Permanently blocked IPs
        self.temp_blocked_ips: Dict[str, float] = {}  # IP -> block_until_timestamp
        
        # Configuration
        self.max_requests_per_minute = 120  # Increased for video generation workloads
        self.max_requests_per_second = 25   # Increased burst protection for API-heavy operations
        self.suspicious_threshold = 5  # Block after 5 suspicious requests
        self.temp_block_duration = 3600  # 1 hour temporary block
        
        # Load persistent blocks on startup
        self._load_persistent_blocks()
        
        self.last_cleanup = time.time()
        
        # Store reference for stats access
        SecurityMiddleware._instance = self
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        client_ip = self._get_client_ip(request)
        
        # Check if IP is blocked
        if self._is_ip_blocked(client_ip):
            logger.warning(f"Blocked IP attempted access: {client_ip}")
            return JSONResponse(
                status_code=403,
                content={"detail": "Access forbidden"}
            )
        
        # Check for suspicious patterns
        is_suspicious = self._is_suspicious_request(request)
        
        if is_suspicious:
            logger.warning(
                f"Suspicious request detected - IP: {client_ip}, "
                f"Method: {request.method}, Path: {request.url.path}, "
                f"User-Agent: {request.headers.get('user-agent', 'Unknown')}"
            )
            
            # Increment suspicious request count
            self.suspicious_count[client_ip] += 1
            
            # Auto-block IP if too many suspicious requests
            if self.suspicious_count[client_ip] >= self.suspicious_threshold:
                self._block_ip_temporarily(client_ip)
                logger.error(f"IP {client_ip} temporarily blocked after {self.suspicious_count[client_ip]} suspicious requests")
                return JSONResponse(
                    status_code=403,
                    content={"detail": "IP temporarily blocked due to suspicious activity"}
                )
        
        # Enhanced rate limiting check
        rate_limit_result = self._check_rate_limits(client_ip, str(request.url.path))
        if rate_limit_result:
            logger.warning(f"Rate limit exceeded for IP: {client_ip} - {rate_limit_result}")
            return JSONResponse(
                status_code=429,
                content={"detail": f"Rate limit exceeded: {rate_limit_result}"}
            )
        
        # Process the request
        response = await call_next(request)
        
        # Log 404s and security events
        if response.status_code == 404:
            if self.log_all_404s or is_suspicious:
                logger.info(
                    f"404 Not Found - IP: {client_ip}, "
                    f"Method: {request.method}, Path: {request.url.path}, "
                    f"User-Agent: {request.headers.get('user-agent', 'Unknown')}, "
                    f"Suspicious: {is_suspicious}"
                )
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Log response time for monitoring
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        # Check for forwarded headers (common in reverse proxy setups)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"
    
    def _is_suspicious_request(self, request: Request) -> bool:
        """Check if request matches suspicious patterns"""
        path = request.url.path.lower()
        query = str(request.url.query).lower() if request.url.query else ""
        
        # Check path against patterns
        for pattern in self.COMPILED_PATTERNS:
            if pattern.search(path) or pattern.search(query):
                return True
        
        # Check for common attack indicators in headers
        user_agent = request.headers.get("user-agent", "").lower()
        if any(bot in user_agent for bot in ["sqlmap", "nikto", "nmap", "masscan"]):
            return True
        
        return False
    
    def _is_ip_blocked(self, client_ip: str) -> bool:
        """Check if IP is permanently or temporarily blocked"""
        current_time = time.time()
        
        # Check permanent blocks
        if client_ip in self.blocked_ips:
            return True
        
        # Check temporary blocks
        if client_ip in self.temp_blocked_ips:
            if current_time < self.temp_blocked_ips[client_ip]:
                return True
            else:
                # Block expired, remove it
                del self.temp_blocked_ips[client_ip]
                self.suspicious_count[client_ip] = 0  # Reset suspicious count
                logger.info(f"Temporary block expired for IP: {client_ip}")
        
        return False
    
    def _block_ip_temporarily(self, client_ip: str):
        """Add IP to temporary block list"""
        block_until = time.time() + self.temp_block_duration
        self.temp_blocked_ips[client_ip] = block_until
        logger.warning(f"IP {client_ip} temporarily blocked until {time.ctime(block_until)}")
    
    def _block_ip_permanently(self, client_ip: str):
        """Add IP to permanent block list"""
        self.blocked_ips.add(client_ip)
        logger.error(f"IP {client_ip} permanently blocked")
    
    def _check_rate_limits(self, client_ip: str, request_path: str = "") -> str | None:
        """Enhanced rate limiting with burst protection"""
        # Exempt critical paths from rate limiting
        exempt_paths = ["/health", "/docs", "/openapi.json", "/api/v1/auth/", "/admin/login", "/admin/verify"]
        if any(request_path.startswith(path) for path in exempt_paths):
            return None

        current_time = time.time()

        # Cleanup old entries every 5 minutes
        if current_time - self.last_cleanup > 300:
            self._cleanup_rate_limit_data(current_time)
            self.last_cleanup = current_time
        
        # Exemptions for API-heavy video generation operations
        api_heavy_paths = [
            "/mcp/create-short-video",
            "/jobs/",
            "/api/ai/",
            "/api/audio/tts",
            "/api/video/"
        ]
        
        # Apply more lenient limits for API-heavy operations
        if any(path in request_path for path in api_heavy_paths):
            max_per_second = 50  # Higher limit for video generation
            max_per_minute = 300  # Higher minute limit
        else:
            max_per_second = self.max_requests_per_second
            max_per_minute = self.max_requests_per_minute
        
        # Get request queue for this IP
        request_queue = self.request_count[client_ip]
        
        # Remove requests older than 1 minute
        while request_queue and current_time - request_queue[0] > 60:
            request_queue.popleft()
        
        # Add current request
        request_queue.append(current_time)
        
        # Check burst protection (requests per second)
        recent_requests = sum(1 for req_time in request_queue if current_time - req_time < 1)
        if recent_requests > max_per_second:
            return f"Too many requests per second ({recent_requests}/{max_per_second})"
        
        # Check rate limit (requests per minute)
        if len(request_queue) > max_per_minute:
            return f"Too many requests per minute ({len(request_queue)}/{max_per_minute})"
        
        return None
    
    def _cleanup_rate_limit_data(self, current_time: float):
        """Clean up old rate limiting data"""
        # Clean up request queues
        for ip in list(self.request_count.keys()):
            request_queue = self.request_count[ip]
            # Remove requests older than 1 minute
            while request_queue and current_time - request_queue[0] > 60:
                request_queue.popleft()
            # Remove empty queues
            if not request_queue:
                del self.request_count[ip]
        
        # Clean up expired temporary blocks
        expired_blocks = [
            ip for ip, block_until in self.temp_blocked_ips.items()
            if current_time >= block_until
        ]
        for ip in expired_blocks:
            del self.temp_blocked_ips[ip]
            self.suspicious_count[ip] = 0
            logger.info(f"Temporary block expired for IP: {ip}")
        
        # Clean up old suspicious counts
        for ip in list(self.suspicious_count.keys()):
            if ip not in self.temp_blocked_ips and ip not in self.blocked_ips:
                # Reset suspicious count for IPs that aren't blocked
                if self.suspicious_count[ip] > 0 and current_time % 3600 < 60:  # Reset every hour
                    self.suspicious_count[ip] = max(0, self.suspicious_count[ip] - 1)
    
    def get_security_stats(self) -> Dict:
        """Get current security statistics"""
        current_time = time.time()
        return {
            "permanently_blocked_ips": len(self.blocked_ips),
            "temporarily_blocked_ips": len(self.temp_blocked_ips),
            "active_rate_limits": len(self.request_count),
            "suspicious_ips": len([ip for ip, count in self.suspicious_count.items() if count > 0]),
            "temp_blocks_remaining": {
                ip: int(block_until - current_time) 
                for ip, block_until in self.temp_blocked_ips.items()
                if block_until > current_time
            }
        }
    
    def _load_persistent_blocks(self):
        """Load permanently blocked IPs from persistent storage"""
        try:
            from app.utils.security_admin import security_admin
            self.blocked_ips = security_admin.load_persistent_blocks()
            logger.info(f"Loaded {len(self.blocked_ips)} permanently blocked IPs")
        except Exception as e:
            logger.error(f"Error loading persistent blocks: {e}")
    
    @classmethod
    def get_instance(cls):
        """Get the current middleware instance"""
        return getattr(cls, '_instance', None)