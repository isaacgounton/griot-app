# API Key Management System

This document describes the complete API key management system implemented in Griot, providing secure user authentication, API key creation, and comprehensive administration features.

## Overview

The API key management system provides:
- **User Management**: Create and manage users with role-based access control
- **API Key Creation**: Generate secure API keys with customizable permissions and limits
- **Dashboard Interface**: Web-based admin dashboard for managing users and keys
- **Database Persistence**: Full PostgreSQL integration with proper schemas
- **Production Ready**: Secure authentication, rate limiting, and audit trails

## Features

### 🔐 User Management
- **Role-based Access Control**: Admin, User, and Viewer roles
- **Secure Authentication**: Password hashing and session management
- **User Profiles**: Full name, email, creation date, and activity tracking
- **Admin Panel**: Create, update, and delete users through web interface

### 🔑 API Key Management
- **Secure Key Generation**: Cryptographically secure API key generation
- **Key Masking**: Keys are masked in UI for security
- **Rate Limiting**: Configurable rate limits per API key
- **Expiration Dates**: Optional key expiration for enhanced security
- **Usage Tracking**: Monitor API key usage and statistics
- **Status Management**: Enable/disable keys without deletion

### 📊 Admin Dashboard
- **Real-time Statistics**: User count, active keys, usage metrics
- **Search and Filtering**: Find users and keys quickly
- **Bulk Operations**: Manage multiple keys and users efficiently
- **Activity Monitoring**: Track user login and API key usage
- **Visual Interface**: Modern Material-UI based dashboard

## API Endpoints

### Dashboard Management
```
GET    /dashboard/stats           # Get dashboard statistics
GET    /dashboard/recent-activity # Get recent system activity
GET    /dashboard/users          # List users with pagination
POST   /dashboard/users          # Create new user
DELETE /dashboard/users/{id}     # Delete user
GET    /dashboard/api-keys       # List API keys with pagination
POST   /dashboard/api-keys       # Create new API key
PUT    /dashboard/api-keys/{id}  # Update API key
DELETE /dashboard/api-keys/{id}  # Delete API key
```

### Authentication
```
GET    /admin                    # Admin login page (redirects to dashboard)
POST   /admin/login              # Admin authentication
GET    /admin/verify             # Verify admin session
GET    /admin/logout             # Logout and clear session
```

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    hashed_password VARCHAR(255) NOT NULL,
    role userrole NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    last_login TIMESTAMP WITHOUT TIME ZONE
);
```

### API Keys Table
```sql
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    key_id VARCHAR(36) UNIQUE NOT NULL,      -- Public identifier
    key_hash VARCHAR(255) NOT NULL,          -- Hashed actual key
    name VARCHAR(100) NOT NULL,              -- User-friendly name
    status apikeystatusenum NOT NULL DEFAULT 'active',
    user_id INTEGER NOT NULL REFERENCES users(id),
    rate_limit_per_hour INTEGER,
    monthly_quota INTEGER,
    total_requests INTEGER NOT NULL DEFAULT 0,
    last_used TIMESTAMP WITHOUT TIME ZONE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    expires_at TIMESTAMP WITHOUT TIME ZONE
);
```

## Security Features

### 🔒 Secure Key Storage
- API keys are hashed using SHA-256 before storage
- Only the hash is stored in the database
- Full keys are only shown once during creation
- Keys are masked in all UI interfaces

### 🛡️ Authentication & Authorization
- Session-based authentication with secure HMAC tokens
- Role-based access control (Admin, User, Viewer)
- API key validation for all protected endpoints
- Secure password hashing with SHA-256

### 📈 Rate Limiting & Monitoring
- Configurable rate limits per API key
- Usage tracking and analytics
- Request logging and audit trails
- Automatic key expiration support

## Installation & Setup

### 1. Production Deployment
```bash
# Run the production deployment script
./scripts/deploy-production.sh
```

### 2. Manual Setup
```bash
# Start database and Redis
docker-compose up -d postgres redis

# Build and start the API
docker-compose up --build api

# Optional: Run admin setup script manually
python scripts/setup_admin.py
```

### 3. Environment Variables
Required environment variables:
```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/griot
POSTGRES_DB=griot
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password

# Admin Authentication
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
JWT_SECRET_KEY=your_jwt_secret_key

# API Authentication
API_KEY=your_master_api_key
```

## Usage Examples

### Creating an API Key via Dashboard
1. Access the dashboard: `http://localhost:8000/dashboard`
2. Login with admin credentials
3. Navigate to "API Keys" section
4. Click "Create API Key"
5. Fill in the form:
   - **Name**: Descriptive name for the key
   - **Rate Limit**: Requests per hour (default: 100)
   - **Expires At**: Optional expiration date
6. Click "Create" to generate the key
7. **Important**: Copy the generated key immediately - it won't be shown again

### Using API Keys in Requests
```bash
# Example API request with API key authentication
curl -X POST "http://localhost:8000/api/video/generate" \
  -H "X-API-Key: oui_sk_1234567890abcdef..." \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a video about nature"}'
```

### Managing Users
```bash
# Create a new user via API
curl -X POST "http://localhost:8000/dashboard/users" \
  -H "X-API-Key: your_admin_key" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "role": "user",
    "password": "secure_password"
  }'
```

## Frontend Integration

### React Component Usage
The dashboard provides a complete React-based interface:

```typescript
// API key management is available at /dashboard/api-keys
// Features include:
// - Real-time search and filtering
// - Key visibility toggle (show/hide)
// - Copy to clipboard functionality
// - Create, edit, and delete operations
// - Usage statistics and analytics
```

### Authentication Flow
```typescript
// Frontend authentication example
const authenticateUser = async (username: string, password: string) => {
  const response = await fetch('/admin/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  
  if (response.ok) {
    // Session cookie is set automatically
    // Redirect to dashboard
    window.location.href = '/dashboard';
  }
};
```

## Monitoring & Analytics

### Dashboard Statistics
- Total users and API keys
- Active vs inactive keys
- Usage statistics and trends
- Recent activity logs
- Storage and system information

### API Key Analytics
- Request count per key
- Last usage timestamps
- Rate limit utilization
- Error rates and failures
- Geographic usage patterns (if configured)

## Best Practices

### 🔐 Security
1. **Change Default Passwords**: Always update default admin credentials
2. **Use HTTPS**: Configure SSL certificates for production
3. **Rotate Keys**: Regularly rotate API keys
4. **Monitor Usage**: Watch for unusual API key activity
5. **Limit Permissions**: Use role-based access appropriately

### 🚀 Performance
1. **Rate Limiting**: Set appropriate rate limits per user/key
2. **Caching**: Utilize Redis for session and data caching
3. **Database Optimization**: Index frequently queried fields
4. **Monitoring**: Set up alerts for high usage or errors

### 📊 Management
1. **Naming Convention**: Use descriptive names for API keys
2. **Documentation**: Document key purposes and owners
3. **Cleanup**: Remove unused keys and inactive users
4. **Backup**: Regular database backups
5. **Audit**: Regular security audits and access reviews

## Troubleshooting

### Common Issues

**1. "Failed to load API keys"**
- Check API key authentication in browser
- Verify database connectivity
- Check console for network errors

**2. "Database connection failed"**
- Ensure PostgreSQL is running
- Verify DATABASE_URL environment variable
- Check PostgreSQL logs for errors

**3. "Admin login failed"**
- Verify ADMIN_USERNAME and ADMIN_PASSWORD
- Check JWT_SECRET_KEY configuration
- Clear browser cookies and retry

### Debug Commands
```bash
# Check service status
docker-compose ps

# View API logs
docker-compose logs api

# Check database connectivity
docker-compose exec postgres pg_isready -U postgres

# View Redis status
docker-compose exec redis redis-cli ping
```

## Migration & Upgrades

### Database Migrations
The system automatically handles database migrations on startup:
- Creates required tables if they don't exist
- Updates enum types for new values
- Fixes data inconsistencies

### Backup and Restore
```bash
# Backup database
docker-compose exec postgres pg_dump -U postgres griot > backup.sql

# Restore database
docker-compose exec -T postgres psql -U postgres griot < backup.sql
```

## API Reference

For complete API documentation, visit the interactive API docs at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review application logs
3. Consult the API documentation
4. Check database connectivity and configuration

---

*This API key management system provides enterprise-grade security and management features for the Griot platform.*