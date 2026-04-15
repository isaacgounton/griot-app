# Auth Routes Documentation

This directory contains documentation for authentication-related endpoints in the Media Master API.

## Available Endpoints

### User Login

- **Login**: `POST /auth/login`
- **Check Status**: `GET /auth/status`

## Common Use Cases

### User Authentication

Authenticate users with username and password credentials to obtain an API key for accessing protected endpoints. The authentication system supports default admin credentials that can be configured via environment variables.

### Status Checking

Check the current authentication status to determine if a user needs to log in before accessing the dashboard or other protected resources.

## Authentication Flow

1. **Login Request**: Send POST request to `/auth/login` with username and password
2. **API Key Response**: Receive API key in response if credentials are valid
3. **Subsequent Requests**: Include API key in headers for authenticated endpoints
4. **Status Check**: Use GET `/auth/status` to verify authentication state

## Error Handling

All auth endpoints follow standard HTTP status codes:

- **200**: Successful authentication
- **401**: Invalid username or password
- **500**: Internal server error

## Security Features

- Username/password based authentication
- API key generation for session management
- Environment variable configuration for default credentials
- Secure credential validation</content>
<parameter name="filePath">/media/etugrand/DATA/DEV.ai/Media/griot/docs/auth/README.md
