# Admin API Documentation

The Griot provides comprehensive administrative endpoints for user management, job monitoring, system maintenance, and authentication.

## Overview

Admin endpoints provide:

- **Authentication**: Admin login, session management, and verification
- **User Management**: Create, update, list, and delete user accounts
- **Job Management**: Monitor background jobs, cleanup old jobs, scheduler control, and system statistics
- **System Monitoring**: Track API usage, performance metrics, and health status

## Initial Admin Setup

### Creating the First Admin User

Before using any admin features, you must create the initial admin user. This can only be done once when no admin users exist in the system.

#### Option 1: Using the Setup Script (Recommended)

Run the provided setup script to create your first admin user:

```bash
cd /path/to/griot
python scripts/setup_admin_user.py
```

The script will prompt you for:

- Username
- Email address
- Full name
- Password

#### Option 2: Using the API Directly

Make a POST request to the admin setup endpoint:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/admin/setup" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "secure_password_123",
    "email": "admin@example.com",
    "full_name": "System Administrator"
  }'
```

**Important Security Notes:**

- This endpoint can only be used once (to create the first admin)
- After the first admin is created, this endpoint becomes permanently disabled
- Anyone with access to your API can use this endpoint during initial setup
- For production deployments, consider additional security measures

**Response:**

```json
{
  "success": true,
  "message": "Admin user created successfully! You can now log in with your credentials.",
  "user_id": 1
}
```

### Admin Login

Once the admin user is created, log in using the regular authentication endpoint:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "secure_password_123"
  }'
```

**Response:**

```json
{
  "success": true,
  "message": "Login successful",
  "user_id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "is_verified": true,
  "role": "admin"
}
```

## Authentication

All admin endpoints require authentication. The system supports role-based access control with three user roles:

- **admin**: Full system access and user management
- **user**: Standard access with limited admin features
- **viewer**: Read-only access

### Session-Based Authentication

After logging in, use the session cookie for subsequent requests, or include the authentication token in the `Authorization` header.

### API Key Authentication (Legacy)

Some endpoints still support API key authentication via the `X-API-Key` header for backward compatibility:

```bash
-H "X-API-Key: your_api_key"
```

## Base URLs

- **Authentication**: `/api/v1/auth`
- **User Management**: `/api/v1/admin/users`
- **Job Management**: `/api/v1/admin/jobs`

## Authentication API

### Admin Login

Authenticate admin user and establish session using the standard login endpoint.

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "your_password"
  }'
```

**Request Model:**

```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**

```json
{
  "success": true,
  "message": "Login successful",
  "user_id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "is_verified": true,
  "role": "admin"
}
```

### Verify Admin Session

Check if current user session is valid and has admin privileges.

```bash
curl -X GET "http://localhost:8000/api/v1/auth/status"
```

**Response:**

```json
{
  "isAuthenticated": true,
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin"
  }
}
```

### Admin Logout

Clear user session and cookies.

```bash
curl -X POST "http://localhost:8000/api/v1/auth/logout"
```

## User Management API

## User Management API

### Create User

Create a new user account with specified role and permissions.

```bash
curl -X POST "http://localhost:8000/api/v1/admin/users/" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "newuser",
    "full_name": "John Doe",
    "password": "secure_password",
    "role": "user",
    "is_active": true
  }'
```

**Request Model:**

```json
{
  "email": "string",
  "username": "string (optional)",
  "full_name": "string (optional)",
  "password": "string",
  "role": "admin | user | viewer",
  "is_active": "boolean"
}
```

### List Users

Retrieve paginated list of all users with filtering options.

```bash
curl -X GET "http://localhost:8000/api/v1/admin/users/?page=1&limit=50&search=john&role=user" \
  -H "X-API-Key: your_api_key"
```

**Query Parameters:**

- `page`: Page number (default: 1)
- `limit`: Number of users per page (default: 50, max: 100)
- `search`: Search by email, username, or full name
- `role`: Filter by user role (admin, user, viewer, all)

**Response:**

```json
{
  "success": true,
  "data": {
    "users": [...],
    "pagination": {
      "page": 1,
      "limit": 50,
      "total": 150,
      "pages": 3
    }
  }
}
```

### Get User Statistics

Get comprehensive user statistics.

```bash
curl -X GET "http://localhost:8000/api/v1/admin/users/stats" \
  -H "X-API-Key: your_api_key"
```

**Response:**

```json
{
  "success": true,
  "stats": {
    "total_users": 150,
    "active_users": 142,
    "inactive_users": 8,
    "role_distribution": {
      "admin": 5,
      "user": 130,
      "viewer": 15
    }
  }
}
```

### Get User Details

Retrieve detailed information about a specific user.

```bash
curl -X GET "http://localhost:8000/api/v1/admin/users/{user_id}" \
  -H "X-API-Key: your_api_key"
```

### Update User

Update user information and permissions.

```bash
curl -X PUT "http://localhost:8000/api/v1/admin/users/{user_id}" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Smith",
    "role": "admin",
    "is_active": false
  }'
```

### Delete User

Remove a user account.

```bash
curl -X DELETE "http://localhost:8000/api/v1/admin/users/{user_id}" \
  -H "X-API-Key: your_api_key"
```

### Authenticate User

Authenticate a user with email and password.

```bash
curl -X POST "http://localhost:8000/api/v1/admin/users/authenticate" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "user_password"
  }'
```

**Response:**

```json
{
  "success": true,
  "message": "Authentication successful",
  "user": {
    "id": 123,
    "email": "user@example.com",
    "username": "johndoe",
    "full_name": "John Doe",
    "role": "user",
    "is_active": true
  }
}
```

## Job Management API

### Manual Job Cleanup

Trigger immediate cleanup of old completed jobs.

```bash
curl -X POST "http://localhost:8000/api/v1/admin/jobs/cleanup?max_age_hours=48" \
  -H "X-API-Key: your_api_key"
```

**Parameters:**

- `max_age_hours`: Jobs older than this will be deleted (default: 24)

**Response:**

```json
{
  "success": true,
  "message": "Job cleanup completed successfully. Deleted 150 jobs.",
  "max_age_hours": 48,
  "duration_seconds": 2.5,
  "timestamp": "2024-01-15T10:30:00Z",
  "cleanup_stats": {
    "total_deleted": 150
  }
}
```

### Get Cleanup Status

Check current cleanup and scheduler status.

```bash
curl -X GET "http://localhost:8000/api/v1/admin/jobs/cleanup/status" \
  -H "X-API-Key: your_api_key"
```

**Response:**

```json
{
  "scheduler": {
    "running": true,
    "last_run": "2024-01-15T10:30:00Z",
    "next_run": "2024-01-15T11:30:00Z"
  },
  "job_counts": {
    "pending": 5,
    "processing": 3,
    "completed": 4850,
    "failed": 142
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Trigger Cleanup Now

Trigger immediate cleanup using scheduler service.

```bash
curl -X POST "http://localhost:8000/api/v1/admin/jobs/cleanup/trigger" \
  -H "X-API-Key: your_api_key"
```

**Response:**

```json
{
  "success": true,
  "message": "Cleanup triggered successfully",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Get Job Statistics

Retrieve comprehensive job processing statistics.

```bash
curl -X GET "http://localhost:8000/api/v1/admin/jobs/stats" \
  -H "X-API-Key: your_api_key"
```

**Response:**

```json
{
  "job_counts": {
    "pending": 5,
    "processing": 3,
    "completed": 4850,
    "failed": 142
  },
  "total_jobs": 5000,
  "recent_jobs": 10,
  "scheduler_status": {
    "running": true
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Delete Specific Job

Delete a specific job by ID.

```bash
curl -X DELETE "http://localhost:8000/api/v1/admin/jobs/jobs/{job_id}" \
  -H "X-API-Key: your_api_key"
```

**Response:**

```json
{
  "success": true,
  "message": "Job {job_id} deleted successfully",
  "job_id": "job_123",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Start Scheduler

Start the background job scheduler.

```bash
curl -X POST "http://localhost:8000/api/v1/admin/jobs/scheduler/start" \
  -H "X-API-Key: your_api_key"
```

**Response:**

```json
{
  "success": true,
  "message": "Scheduler started successfully",
  "status": {
    "running": true
  }
}
```

### Stop Scheduler

Stop the background job scheduler.

```bash
curl -X POST "http://localhost:8000/api/v1/admin/jobs/scheduler/stop" \
  -H "X-API-Key: your_api_key"
```

**Response:**

```json
{
  "success": true,
  "message": "Scheduler stopped successfully",
  "status": {
    "running": false
  }
}
```

## User Roles and Permissions

### Role Hierarchy

The system uses database-backed user accounts with role-based access control:

1. **Admin**: Full system access
   - Create/modify/delete users
   - Access all admin endpoints
   - View all jobs and data
   - System configuration
   - Manage API keys

2. **User**: Standard access
   - Create content and jobs
   - Access their own data
   - Limited admin viewing
   - Use API keys for programmatic access

3. **Viewer**: Read-only access
   - View public content
   - No creation permissions
   - Limited API access

### Permission Matrix

| Action | Admin | User | Viewer |
|--------|-------|------|--------|
| Create Users | ✅ | ❌ | ❌ |
| Manage Jobs | ✅ | Own Only | ❌ |
| System Stats | ✅ | Limited | ❌ |
| Content Creation | ✅ | ✅ | ❌ |
| API Access | Full | Standard | Limited |
| User Registration | ✅ | ❌ | ❌ |

### User Registration

Regular users can register through the public registration endpoint:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Doe",
    "email": "john@example.com",
    "username": "johndoe",
    "password": "secure_password"
  }'
```

Users must verify their email before they can log in. An admin can also create users directly through the admin API.

## System Monitoring API

### Get Admin Statistics

Get dashboard statistics including job counts and system status.

```bash
curl -X GET "http://localhost:8000/api/v1/admin/stats" \
  -H "Authorization: Bearer your_token"
```

**Response:**

```json
{
  "active_jobs": 5,
  "completed_jobs": 4850,
  "failed_jobs": 142,
  "redis_connected": true
}
```

### Get Recent Jobs

Get list of recent jobs with status information.

```bash
curl -X GET "http://localhost:8000/api/v1/admin/jobs" \
  -H "Authorization: Bearer your_token"
```

**Response:**

```json
{
  "jobs": [
    {
      "id": "job_123",
      "type": "image_generation",
      "status": "completed",
      "created_at": 1640995200.0,
      "progress": 100
    }
  ]
}
```

### Get System Information

Get system configuration and status information.

```bash
curl -X GET "http://localhost:8000/api/v1/admin/system" \
  -H "Authorization: Bearer your_token"
```

**Response:**

```json
{
  "debug": false,
  "redis_url": "redis://***@redis:6379",
  "s3_bucket": "your-bucket",
  "s3_region": "us-east-1",
  "s3_endpoint": "https://s3.amazonaws.com",
  "kokoro_api": "https://api.kokoro.ai",
  "disk_usage_percent": 23.1,
  "uptime_seconds": 86400
}
```

### API Usage Statistics

Track API endpoint usage and performance.

```bash
curl -X GET "http://localhost:8000/api/v1/admin/usage" \
  -H "Authorization: Bearer your_token"
```

## Error Handling

### Common Error Responses

**User Not Found:**

```json
{
  "detail": "User not found"
}
```

**Invalid Role:**

```json
{
  "detail": "Invalid role. Must be one of: admin, user, viewer"
}
```

**Insufficient Permissions:**

```json
{
  "detail": "Insufficient permissions to perform this action"
}
```

**Validation Error:**

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["email"],
      "msg": "Invalid email format"
    }
  ]
}
```

## Best Practices

### User Management

1. **Use Strong Passwords**: Enforce minimum 8 characters with mixed case
2. **Regular Audits**: Review user accounts monthly
3. **Role-Based Access**: Assign minimum necessary permissions
4. **Account Monitoring**: Track login activities and suspicious behavior

### Job Management

1. **Regular Cleanup**: Schedule automated cleanup of old jobs
2. **Monitor Performance**: Watch for increasing completion times
3. **Error Analysis**: Review failed jobs for patterns
4. **Resource Management**: Monitor storage and processing resources

### Security

1. **Strong Passwords**: Use complex passwords for admin accounts
2. **Regular Audits**: Review user accounts and access logs monthly
3. **Role-Based Access**: Assign minimum necessary permissions
4. **Account Monitoring**: Track login activities and suspicious behavior
5. **Session Management**: Use secure session handling and timeouts
6. **Email Verification**: Ensure all users verify their email addresses

### Database-Backed Authentication

The system now uses a PostgreSQL database for user management:

- **User Registration**: Public registration with email verification
- **Admin Setup**: One-time initial admin creation
- **Role Management**: Database-stored user roles and permissions
- **Session Security**: JWT-based authentication with proper validation

### Frontend Role Protection

The frontend implements role-based UI visibility:

- **Admin Features Hidden**: System settings, debug tools, system information, job cleanup operations, and job deletion are only visible to admin users
- **Role Checking**: User roles are validated on the frontend before displaying sensitive features
- **Graceful Degradation**: Non-admin users see appropriate messaging about restricted features
- **Job Management**: Regular users can view jobs and schedule completed jobs to social media, but cannot delete or retry jobs

**Note**: While frontend protection prevents unauthorized access to admin features, backend endpoints currently use API key authentication without additional role validation. For enhanced security, consider implementing user-specific API keys with role-based backend protection in future updates.

## Troubleshooting

### Common Issues

**Database Connection Errors:**

```bash
# Check database status
curl -X GET "http://localhost:8000/api/v1/admin/health"
```

**Job Queue Performance Issues:**

```bash
# Check job statistics
curl -X GET "http://localhost:8000/api/v1/admin/jobs/stats"

# Manual cleanup if needed
curl -X POST "http://localhost:8000/api/v1/admin/jobs/cleanup"
```

**User Authentication Problems:**

```bash
# Verify user exists and is active
curl -X GET "http://localhost:8000/api/v1/admin/users/{user_id}"
```

### Performance Optimization

1. **Database Indexing**: Ensure proper indexes on user and job tables
2. **Connection Pooling**: Configure appropriate database connections
3. **Caching**: Implement Redis caching for frequently accessed data
4. **Background Processing**: Use job queues for heavy operations

---

*For technical implementation details, see the source code in `app/routes/auth/auth.py`, `app/routes/admin/admin_users.py`, and `app/routes/admin/admin_jobs.py`*
