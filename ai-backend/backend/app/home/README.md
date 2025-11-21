# Home Module

This module implements client-side functionality for AI dialogues with data analysis capabilities through MCP service integration.

## Features

- User authentication (login, registration, token refresh)
- AI Chat with conversation history
- Integration with MCP service for data querying
- Automatic intent detection for data queries
- Support for multiple AI models through the existing AI model configuration

## Components

### Authentication
- `ClientUser`: User model for client-side authentication
- Login and registration with CAPTCHA verification
- JWT-based authentication with refresh token support
- Password hashing and secure token management

### Models
- `AIChat`: Stores chat sessions
- `AIChatMessage`: Stores individual messages in chat sessions
- `MCPQuery`: Tracks data queries made through the MCP service

### Services
- `AuthService`: Manages authentication and token handling
- `AIChatService`: Manages AI chats and dialogues
- `MCPClient`: Client for interacting with the MCP service

### API Endpoints

#### Authentication
- `/home/auth/captcha/image`: Get CAPTCHA image for registration/login
- `/home/auth/login`: Login with username, password and CAPTCHA
- `/home/auth/register`: Register a new user account
- `/home/auth/refresh-token`: Refresh the access token
- `/home/auth/logout`: User logout
- `/home/auth/me`: Get current user information
- `/home/auth/check-username/{username}`: Check if username is available

#### Chat
- `/home/chat`: CRUD operations for chat sessions
- `/home/chat/{chat_id}/messages`: Get messages for a chat
- `/home/chat/completion`: Process a chat completion request

## Usage

### Authentication

#### Registration
```python
# First get CAPTCHA
response = client.get("/home/auth/captcha/image")
captcha_data = response.json()["data"]
captcha_id = captcha_data["captcha_id"]
# Display captcha_data["image_base64"] to user

# Register with the CAPTCHA
response = client.post("/home/auth/register", json={
    "username": "new_user",
    "email": "user@example.com",
    "password": "secure_password",
    "full_name": "New User",
    "captcha": "ABCD",  # User input from CAPTCHA image
    "captcha_id": captcha_id
})
```

#### Login
```python
# First get CAPTCHA
response = client.get("/home/auth/captcha/image")
captcha_data = response.json()["data"]
captcha_id = captcha_data["captcha_id"]
# Display captcha_data["image_base64"] to user

# Login with the CAPTCHA
response = client.post("/home/auth/login", json={
    "username": "user",
    "password": "password",
    "captcha": "ABCD",  # User input from CAPTCHA image
    "captcha_id": captcha_id
})
token_data = response.json()
access_token = token_data["access_token"]
```

### Creating a Chat Session
```python
response = client.post("/home/chat",
    headers={"Authorization": f"Bearer {access_token}"},
    json={
        "title": "New Chat",
        "model_id": "model_id_here"
    }
)
chat_id = response.json()["id"]
```

### Sending a Message
```python
response = client.post("/home/chat/completion",
    headers={"Authorization": f"Bearer {access_token}"},
    json={
        "chat_id": chat_id,
        "message": "Show me the latest transaction data for customer 12345",
        "enable_mcp_query": True
    }
)
```

The system will:
1. Analyze the message for query intent
2. If a data query is detected, it will call the MCP service
3. Add the query results to the context
4. Generate an AI response using the context
5. Store both user and assistant messages

## MCP Service Integration

The MCP service integration allows the AI to query external data sources when needed. This is done through two main functions:

1. `analyze_query_intent`: Analyzes user messages to detect query intent
2. `query_data`: Executes queries against the MCP service

The MCP service should expose two endpoints:
- `/api/v1/analyze/intent`: Analyzes messages for query intent
- `/api/v1/query/{query_type}`: Executes queries of the specified type

## Configuration

Configure the MCP service connection in `.env`:
```
MCP_SERVICE_URL=http://mcp-service-url
MCP_API_KEY=your-api-key
```

Or set these environment variables directly.

## Authentication Security

The home module uses JWT-based authentication with the following security features:

1. Passwords are securely hashed using bcrypt
2. Access tokens expire after a configurable period
3. Refresh tokens allow obtaining new access tokens
4. Token revocation on logout
5. CAPTCHA verification for login and registration to prevent brute force attacks
6. Rate limiting on authentication endpoints
