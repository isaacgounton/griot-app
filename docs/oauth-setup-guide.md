# OAuth Setup Guide with Authlib

Complete guide for setting up OAuth authentication (Google, GitHub, Discord) using Authlib.

## ✅ What's Been Implemented

### Backend (Complete)
- ✅ **Authlib integration** - Pure Python OAuth library
- ✅ **OAuth configuration** (`app/utils/oauth_config.py`)
- ✅ **OAuth routes** (`app/routes/auth/oauth.py`)
- ✅ **Database models** - `OAuthAccount` table for linking providers
- ✅ **JWT authentication** - Stateless token-based auth
- ✅ **User creation** - Auto-create users from OAuth providers
- ✅ **Account linking** - Link OAuth accounts to existing users

### Supported Providers
- ✅ **Google** - Sign in with Google
- ✅ **GitHub** - Sign in with GitHub
- ✅ **Discord** - Sign in with Discord

---

## 🔧 Configuration

### 1. Environment Variables

Add these to your `.env` file:

```bash
# Base URLs
BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173

# JWT Secret (already configured)
JWT_SECRET_KEY=your-secret-key
# Or use:
BETTER_AUTH_SECRET=your-secret-key

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# GitHub OAuth (Optional)
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# Discord OAuth (Optional)
DISCORD_CLIENT_ID=your-discord-client-id
DISCORD_CLIENT_SECRET=your-discord-client-secret
```

### 2. Get OAuth Credentials

#### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable **Google+ API**
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Application type: **Web application**
6. Authorized redirect URIs:
   ```
   http://localhost:8000/api/v1/auth/oauth/google/callback
   https://your-domain.com/api/v1/auth/oauth/google/callback
   ```
7. Copy **Client ID** and **Client Secret**

#### GitHub OAuth Setup

1. Go to **GitHub Settings** → **Developer settings** → **OAuth Apps**
2. Click **New OAuth App**
3. Fill in:
   - Application name: `Your App Name`
   - Homepage URL: `http://localhost:5173`
   - Authorization callback URL: `http://localhost:8000/api/v1/auth/oauth/github/callback`
4. Copy **Client ID** and generate **Client Secret**

#### Discord OAuth Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **New Application**
3. Go to **OAuth2** section
4. Add redirect:
   ```
   http://localhost:8000/api/v1/auth/oauth/discord/callback
   ```
5. Copy **Client ID** and **Client Secret**

### 3. Database Migration

Run the database migration to create the `oauth_accounts` table:

```bash
# The table will be automatically created on first run due to SQLAlchemy's create_all()
# Or run a proper migration with Alembic:

# Generate migration
alembic revision --autogenerate -m "Add OAuth accounts table"

# Apply migration
alembic upgrade head
```

**OAuthAccount Table Schema:**
```sql
CREATE TABLE oauth_accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    provider VARCHAR(50) NOT NULL,
    provider_user_id VARCHAR(255) NOT NULL,
    provider_email VARCHAR(255),
    provider_name VARCHAR(255),
    provider_avatar VARCHAR(500),
    access_token VARCHAR(500),
    refresh_token VARCHAR(500),
    token_expires_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    UNIQUE(user_id, provider)
);
```

---

## 🚀 API Endpoints

### Get Available Providers

```bash
GET /api/v1/auth/oauth/providers
```

**Response:**
```json
{
  "success": true,
  "providers": ["google", "github", "discord"],
  "available": {
    "google": true,
    "github": true,
    "discord": false
  }
}
```

### Initiate OAuth Login

```bash
GET /api/v1/auth/oauth/{provider}/login
```

**Example:**
```bash
# Redirect user to:
http://localhost:8000/api/v1/auth/oauth/google/login
```

This will:
1. Redirect to Google's login page
2. User authorizes your app
3. Google redirects back to callback URL
4. User is logged in with JWT token

### OAuth Callback (Handled automatically)

```bash
GET /api/v1/auth/oauth/{provider}/callback
```

This endpoint:
1. Receives authorization code from provider
2. Exchanges code for access token
3. Fetches user info
4. Creates/logs in user
5. Sets JWT cookie
6. Redirects to frontend with token

---

## 🎨 Frontend Integration

### React Example

```tsx
// src/pages/Login.tsx
import { useState } from 'react';

function Login() {
  const API_BASE = 'http://localhost:8000/api/v1';

  const handleGoogleLogin = () => {
    // Redirect to OAuth endpoint
    window.location.href = `${API_BASE}/auth/oauth/google/login`;
  };

  const handleGitHubLogin = () => {
    window.location.href = `${API_BASE}/auth/oauth/github/login`;
  };

  const handleDiscordLogin = () => {
    window.location.href = `${API_BASE}/auth/oauth/discord/login`;
  };

  return (
    <div className="login-container">
      <h1>Login to Griot</h1>

      {/* OAuth Buttons */}
      <div className="oauth-buttons">
        <button onClick={handleGoogleLogin} className="btn-google">
          <img src="/google-icon.svg" alt="Google" />
          Continue with Google
        </button>

        <button onClick={handleGitHubLogin} className="btn-github">
          <img src="/github-icon.svg" alt="GitHub" />
          Continue with GitHub
        </button>

        <button onClick={handleDiscordLogin} className="btn-discord">
          <img src="/discord-icon.svg" alt="Discord" />
          Continue with Discord
        </button>
      </div>

      <div className="divider">or</div>

      {/* Email/Password Form */}
      <form onSubmit={handleEmailLogin}>
        <input type="email" placeholder="Email" />
        <input type="password" placeholder="Password" />
        <button type="submit">Login</button>
      </form>
    </div>
  );
}
```

### OAuth Callback Handler

Create a page to handle the OAuth redirect:

```tsx
// src/pages/AuthCallback.tsx
import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

function AuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  useEffect(() => {
    const token = searchParams.get('token');
    const error = searchParams.get('error');
    const success = searchParams.get('success');

    if (success === 'true' && token) {
      // Store token (optional - already in HTTP-only cookie)
      localStorage.setItem('access_token', token);

      // Redirect to dashboard
      navigate('/dashboard');
    } else if (error) {
      const message = searchParams.get('message') || 'OAuth login failed';
      console.error('OAuth error:', message);
      navigate('/login?error=' + encodeURIComponent(message));
    } else {
      navigate('/login');
    }
  }, [searchParams, navigate]);

  return (
    <div className="auth-callback">
      <p>Completing authentication...</p>
    </div>
  );
}

export default AuthCallback;
```

### Router Configuration

```tsx
// src/App.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Login from './pages/Login';
import AuthCallback from './pages/AuthCallback';
import Dashboard from './pages/Dashboard';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/auth/callback" element={<AuthCallback />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </BrowserRouter>
  );
}
```

---

## 🔒 Security Notes

### Current Implementation

- ✅ **JWT tokens** - Stateless, signed tokens
- ✅ **HTTP-only cookies** - Protected from XSS
- ✅ **HTTPS recommended** - Secure transport
- ✅ **Email verification** - OAuth emails are pre-verified
- ✅ **Provider validation** - Only configured providers allowed

### Production Recommendations

1. **Store tokens securely:**
   ```python
   # Encrypt OAuth access/refresh tokens before storing
   from cryptography.fernet import Fernet

   key = os.getenv("ENCRYPTION_KEY")
   cipher = Fernet(key)
   encrypted_token = cipher.encrypt(token.encode())
   ```

2. **Use HTTPS:**
   ```python
   # Update in app/utils/jwt_auth.py
   set_auth_cookie(response, access_token, secure=True)
   ```

3. **Configure CORS properly:**
   ```python
   # In app/main.py
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://your-frontend.com"],  # Specific origins only!
       allow_credentials=True,
       allow_methods=["GET", "POST"],
       allow_headers=["*"],
   )
   ```

4. **Rate limiting on OAuth endpoints:**
   ```python
   @router.get("/{provider}/login")
   @limiter.limit("5/minute")  # Max 5 OAuth attempts per minute
   async def oauth_login(...):
       ...
   ```

---

## 🧪 Testing

### Test OAuth Flow

```bash
# 1. Check configured providers
curl http://localhost:8000/api/v1/auth/oauth/providers

# 2. Initiate Google login (in browser)
open http://localhost:8000/api/v1/auth/oauth/google/login

# 3. After callback, check cookie
curl http://localhost:8000/api/v1/auth/profile \
  --cookie "access_token=Bearer_your_jwt_token"
```

### Verify Database

```sql
-- Check users created via OAuth
SELECT id, username, email, is_verified, hashed_password
FROM users
WHERE hashed_password IS NULL;  -- OAuth users have no password

-- Check OAuth accounts
SELECT u.username, u.email, oa.provider, oa.provider_email
FROM users u
JOIN oauth_accounts oa ON u.id = oa.user_id;
```

---

## 🎯 User Flow Examples

### New User with Google

1. User clicks "Continue with Google"
2. Redirected to Google login
3. User authorizes app
4. System creates:
   - New `User` with email from Google
   - New `OAuthAccount` linking user to Google
5. User is logged in with JWT token
6. Redirected to dashboard

### Existing User with Google

1. User already has account with email `user@example.com`
2. User clicks "Continue with Google" with same email
3. System finds existing user by email
4. Creates `OAuthAccount` linking existing user to Google
5. User is logged in
6. Next time, login is instant!

### User with Multiple OAuth Providers

1. User registers with Google → Creates account
2. Later, connects GitHub → Links GitHub to same account
3. User can now log in with either Google OR GitHub
4. Both point to same user account

---

## 🐛 Troubleshooting

### "OAuth provider not configured"

**Problem:** `GOOGLE_CLIENT_ID` or `GOOGLE_CLIENT_SECRET` not set.

**Solution:**
```bash
# Check .env file
cat .env | grep GOOGLE

# Restart server after adding credentials
docker-compose restart api
```

### "Redirect URI mismatch"

**Problem:** OAuth provider's redirect URI doesn't match your callback URL.

**Solution:**
1. Check your provider settings (Google/GitHub/Discord console)
2. Ensure callback URL is exactly:
   ```
   http://localhost:8000/api/v1/auth/oauth/{provider}/callback
   ```
3. Include both `http://localhost:8000` and your production domain

### "Email already exists"

**Problem:** User tries OAuth login but email already exists with password login.

**Solution:**
This is handled automatically! The system will:
1. Find existing user by email
2. Link OAuth account to existing user
3. Log user in

### CORS errors

**Problem:** Frontend can't access OAuth endpoints.

**Solution:**
```python
# In app/main.py - ensure frontend URL is in CORS origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    ...
)
```

---

## 📊 Comparison: OAuth vs Email/Password

| Feature | Email/Password | OAuth (Google/GitHub) |
|---------|---------------|----------------------|
| Setup time | 0 minutes (done) | 5 minutes |
| User friction | High (form filling) | Low (one click) |
| Email verification | Required | Pre-verified ✅ |
| Password reset | Required | Not needed ✅ |
| Security | You manage passwords | Provider manages ✅ |
| Trust factor | Lower | Higher ✅ |
| Adoption rate | ~30% | ~70% ✅ |

**Recommendation:** Offer both! OAuth for convenience, email/password for privacy-conscious users.

---

## 🚀 Next Steps

1. ✅ **Test Google OAuth** - Set up Google credentials and test login
2. ⚠️ **Add GitHub/Discord** - Optional but recommended
3. 📱 **Update frontend** - Add OAuth buttons to login page
4. 🔒 **Enable HTTPS** - Required for production OAuth
5. 📊 **Monitor usage** - Track which providers users prefer
6. 🎨 **Custom branding** - Customize OAuth consent screen

---

## 📚 Additional Resources

- [Authlib Documentation](https://docs.authlib.org/)
- [Google OAuth Guide](https://developers.google.com/identity/protocols/oauth2)
- [GitHub OAuth Guide](https://docs.github.com/en/apps/oauth-apps)
- [Discord OAuth Guide](https://discord.com/developers/docs/topics/oauth2)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
