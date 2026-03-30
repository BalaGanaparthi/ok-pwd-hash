# Okta Password Hash User Creator

A Python tool that creates Okta users with hashed passwords and validates authentication.

## Features

- Generates random 16-character passwords
- Supports SHA-1, SHA-256, and SHA-512 hashing algorithms
- Creates users in Okta using the Management API with pre-hashed passwords
- Validates credentials using the `/authn` endpoint

## Prerequisites

- Python 3.8+ (for local execution)
- Docker (for containerized execution)
- Okta developer account with API token
- API token must have user management permissions

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OKTA_DOMAIN` | Your Okta domain | `dev-123456.okta.com` |
| `OKTA_API_TOKEN` | Okta API token with user management permissions | `00abc123...` |

## Usage

### Option 1: Run with Docker

```bash
# Build the Docker image
docker build -t okta-password-hash .

# Run the container
docker run -it \
  -e OKTA_DOMAIN="dev-123456.okta.com" \
  -e OKTA_API_TOKEN="your-api-token" \
  okta-password-hash
```

### Option 2: Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OKTA_DOMAIN="dev-123456.okta.com"
export OKTA_API_TOKEN="your-api-token"

# Run the script
python okta_password_hash.py
```

## Interactive Prompts

The program will prompt you for:

1. **Username** - Must be in email format (e.g., `user@example.com`)
2. **First Name** - User's first name
3. **Last Name** - User's last name
4. **Algorithm** - Choose from:
   - `1` - SHA-1
   - `2` - SHA-256
   - `3` - SHA-512

## Example Session

```
============================================================
Okta User Creation with Hashed Password
============================================================

Okta Domain: dev-123456.okta.com

Enter username (email format): testuser@example.com
Enter first name: Test
Enter last name: User

Select hashing algorithm:
1. SHA-1
2. SHA-256
3. SHA-512

Enter your choice (1-3): 2

------------------------------------------------------------
Generated Credentials
------------------------------------------------------------
Password (clear text): xK8#mP2nQ5vL9wBz
Algorithm: SHA-256
Salt (base64): R0lGODlhAQABAAAAADs=
Hash (base64): 6ONMDzdYZltRuM8j0EaG0eUgY0ooPj/m09MqlnGJ3AQ=

------------------------------------------------------------
Creating User in Okta
------------------------------------------------------------
User created successfully!
User ID: 00u1234567890abcdef
Status: ACTIVE

------------------------------------------------------------
Validating Credentials via /authn
------------------------------------------------------------
Authentication successful!
Status: SUCCESS
Session Token: 20111DkXk3v...

============================================================
Summary
============================================================
Username: testuser@example.com
Password: xK8#mP2nQ5vL9wBz
Algorithm: SHA-256
User created and authenticated successfully!
============================================================
```

## How It Works

1. **Password Generation**: Creates a random 16-character password using letters, digits, and special characters (`!@#$%^&*`)

2. **Salt Generation**: Generates a random 16-byte salt

3. **Hashing**: Combines password + salt (POSTFIX order) and hashes with the selected algorithm

4. **User Creation**: Calls Okta Management API `POST /api/v1/users` with the hash:
   ```json
   {
     "credentials": {
       "password": {
         "hash": {
           "algorithm": "SHA-256",
           "salt": "<base64-encoded-salt>",
           "saltOrder": "POSTFIX",
           "value": "<base64-encoded-hash>"
         }
       }
     }
   }
   ```

5. **Validation**: Authenticates using `POST /api/v1/authn` with the clear text password

## Supported Algorithms

| Algorithm | Hash Length | Security Level |
|-----------|-------------|----------------|
| SHA-1 | 160 bits | Legacy (not recommended) |
| SHA-256 | 256 bits | Recommended |
| SHA-512 | 512 bits | Highest security |

## API References

- [Okta Create User API](https://developer.okta.com/docs/api/openapi/okta-management/management/tags/user/)
- [Okta Primary Authentication API](https://developer.okta.com/docs/reference/api/authn/#primary-authentication)
- [Password Import with Hash](https://developer.okta.com/blog/2021/03/05/ultimate-guide-to-password-hashing-in-okta)

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid API token | Check `OKTA_API_TOKEN` is correct |
| `403 Forbidden` | Insufficient permissions | Ensure token has user management scope |
| `400 Bad Request` | User already exists | Use a different username |
| `Authentication failed` | Hash mismatch | Verify salt order is POSTFIX |
