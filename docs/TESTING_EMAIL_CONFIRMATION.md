# Testing Email Confirmation System

## Quick Start Testing

### 1. Start the Infrastructure

```bash
cd /media/etugrand/DATA/DEV.ai/Griot/griot

# Terminal 1: Start Docker containers + backend
bash start_backend_with_redis_docker.sh

# Wait for:
# ✓ PostgreSQL is healthy
# ✓ Redis is healthy
# ✓ Backend API listening on http://localhost:8000
```

### 2. Start the Frontend

```bash
# Terminal 2: Start frontend dev server
cd frontend
npm run dev

# Wait for:
# ✓ Vite dev server running on http://localhost:5173
```

### 3. Test Registration Flow

#### Step 1: Visit Registration Page

```
http://localhost:5173/register
```

#### Step 2: Fill Registration Form

- **Full Name**: John Doe
- **Email**: <john@example.com> (use a real email you can check)
- **Username**: johndoe
- **Password**: SecurePass123!
- **Confirm Password**: SecurePass123!
- Check "I agree to Terms of Service"

#### Step 3: Click Register Button

Expected result:

```
✅ Success: "Registration successful! Please check your email to verify your account."
✅ Redirects to /login after 2 seconds
```

#### Step 4: Check Your Email

- Look for email from: `hello@etugrand.com` (or your EMAIL_FROM_ADDRESS)
- Subject: "Verify your ETUGRAND email address"
- Click the "Verify Email Address" button
- Or copy the verification link

#### Step 5: Verify Email

Two options:

**Option A: Click email button**

- Opens link like: `http://localhost:5173/verify-email?token=ABC123...`
- Should show: "Email verified successfully!"

**Option B: Manual API call**

```bash
curl -X POST http://localhost:8000/api/v1/auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{"token": "YOUR_TOKEN_HERE"}'
```

Expected response:

```json
{
  "success": true,
  "message": "Email verified successfully! You can now log in with your credentials."
}
```

#### Step 6: Log In

Go to: `http://localhost:5173/login`

- **Username/Email**: johndoe (or <john@example.com>)
- **Password**: SecurePass123!

Expected result:

```
✅ Success: Login successful
✅ Redirects to /dashboard
✅ See user profile info
```

## API Testing with cURL

### Test 1: Register User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Jane Smith",
    "email": "jane@example.com",
    "username": "janesmith",
    "password": "SecurePass123!"
  }'
```

Expected response:

```json
{
  "success": true,
  "message": "Registration successful! Please check your email to verify your account.",
  "user_id": "1"
}
```

### Test 2: Try Login Before Email Verification

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "janesmith",
    "password": "SecurePass123!"
  }'
```

Expected response (403 Forbidden):

```json
{
  "detail": "Please verify your email before logging in. Check your inbox for the verification link."
}
```

### Test 3: Verify Email

```bash
curl -X POST http://localhost:8000/api/v1/auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{"token": "TOKEN_FROM_EMAIL"}'
```

Expected response:

```json
{
  "success": true,
  "message": "Email verified successfully! You can now log in with your credentials."
}
```

### Test 4: Login After Verification

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "janesmith",
    "password": "SecurePass123!"
  }'
```

Expected response (200 OK):

```json
{
  "success": true,
  "message": "Login successful",
  "user_id": 1,
  "username": "janesmith",
  "email": "jane@example.com",
  "is_verified": true
}
```

### Test 5: Check Auth Status

```bash
curl http://localhost:8000/api/v1/auth/status
```

Expected response:

```json
{
  "isAuthenticated": false,
  "message": "Please login to access the dashboard"
}
```

## Error Scenarios to Test

### Scenario 1: Duplicate Email

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Duplicate User",
    "email": "john@example.com",
    "username": "duplicate",
    "password": "SecurePass123!"
  }'
```

Expected: **400 Bad Request**

```json
{"detail": "Email already registered"}
```

### Scenario 2: Duplicate Username

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Another User",
    "email": "another@example.com",
    "username": "johndoe",
    "password": "SecurePass123!"
  }'
```

Expected: **400 Bad Request**

```json
{"detail": "Username already taken"}
```

### Scenario 3: Weak Password

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Weak Pass User",
    "email": "weak@example.com",
    "username": "weakpass",
    "password": "weak"
  }'
```

Expected: **400 Bad Request**

```json
{"detail": "Password must be at least 8 characters"}
```

### Scenario 4: Invalid Email

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Bad Email User",
    "email": "not-an-email",
    "username": "bademail",
    "password": "SecurePass123!"
  }'
```

Expected: **400 Bad Request**

```json
{"detail": "Valid email is required"}
```

### Scenario 5: Wrong Password

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "janesmith",
    "password": "WrongPassword123!"
  }'
```

Expected: **401 Unauthorized**

```json
{"detail": "Invalid username or password"}
```

### Scenario 6: Expired Token

```bash
# Create a token, wait 24+ hours, then try:
curl -X POST http://localhost:8000/api/v1/auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{"token": "EXPIRED_TOKEN"}'
```

Expected: **400 Bad Request**

```json
{"detail": "Verification token has expired. Please request a new one."}
```

## Database Verification

### Check users in database

```bash
docker exec postgres-dev psql -U postgres -d griot -c "SELECT id, username, email, is_verified, created_at FROM users;"
```

### Check user details

```bash
docker exec postgres-dev psql -U postgres -d griot -c "SELECT id, username, email, is_verified, verification_token, verification_token_expires_at FROM users WHERE username='johndoe';"
```

## Frontend Console Debugging

Open DevTools (F12) and check:

1. **Network tab**: Watch registration API call
   - Request: POST `/api/v1/auth/register`
   - Response: 200 with `user_id`

2. **Console tab**: Check for errors
   - Should see successful registration message
   - No 404 errors
   - No CORS errors

3. **Application tab**: Check localStorage
   - After login: `griot_api_key`, `griot_user_role` should be set
   - After logout: Keys should be cleared

## Email Testing Options

### Option 1: Use Real Email (Recommended)

- Configure Resend API key
- Uses real email addresses
- Can test actual email delivery

### Option 2: Mock Email in Development

Edit `/app/utils/email.py`:

```python
async def send_verification_email(...):
    # For testing, just log the token instead of sending
    logger.info(f"TEST: Verification link: http://localhost:5173/verify-email?token={verification_token}")
    return True
```

### Option 3: Email Service Dashboard

- Visit Resend dashboard: <https://resend.com/emails>
- See all sent emails in real-time
- Check delivery status

## Performance Testing

### Test Database Connection Speed

```bash
curl http://localhost:8000/api/v1/auth/status
```

Should respond in **<100ms**

### Test Registration Speed

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{...}' \
  -w "\nTime: %{time_total}s\n"
```

Should complete in **<1 second** (email delivery separate)

## Cleanup Between Tests

### Clear all users

```bash
docker exec postgres-dev psql -U postgres -d griot -c "DELETE FROM users;"
```

### Reset user sequences

```bash
docker exec postgres-dev psql -U postgres -d griot -c "ALTER SEQUENCE users_id_seq RESTART WITH 1;"
```

## Common Issues & Solutions

### "Database not available"

- Check PostgreSQL container: `docker ps | grep postgres`
- Start it: `docker start postgres-dev`

### "Email not sending"

- Check RESEND_API_KEY in .env
- Verify email address in Resend dashboard
- Check backend logs for API errors

### "Verification link doesn't work"

- Copy token from backend logs
- Try manual API call with token
- Check token format (should be 32 alphanumeric chars)

### "Frontend can't reach backend"

- Check backend is running: `curl http://localhost:8000/docs`
- Check CORS headers in response
- Verify VITE_API_BASE_URL in .env

---

**Happy Testing!** 🎉
