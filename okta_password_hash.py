#!/usr/bin/env python3
"""
Okta User Creation with Hashed Password

This script:
1. Generates a random 16-character password
2. Hashes it using SHA-1, SHA-256, or SHA-512 (user's choice)
3. Creates a user in Okta with the hashed password
4. Validates the credentials using /authn endpoint

Required environment variables:
- OKTA_DOMAIN: Your Okta domain (e.g., dev-123456.okta.com)
- OKTA_API_TOKEN: Your Okta API token with user management permissions
"""

import os
import sys
import secrets
import string
import hashlib
import base64
import requests


def generate_random_password(length: int = 16) -> str:
    """Generate a random password with letters, digits, and special characters."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


def generate_random_salt(length: int = 16) -> bytes:
    """Generate random salt bytes."""
    return secrets.token_bytes(length)


def hash_password(password: str, salt: bytes, algorithm: str) -> bytes:
    """Hash the password with salt using the specified algorithm."""
    # Combine password and salt (POSTFIX: password + salt)
    password_bytes = password.encode('utf-8')
    combined = password_bytes + salt

    if algorithm == "SHA-1":
        return hashlib.sha1(combined).digest()
    elif algorithm == "SHA-256":
        return hashlib.sha256(combined).digest()
    elif algorithm == "SHA-512":
        return hashlib.sha512(combined).digest()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")


def create_okta_user(okta_domain: str, api_token: str, username: str,
                     first_name: str, last_name: str,
                     algorithm: str, salt_b64: str, hash_b64: str) -> dict:
    """Create a user in Okta with a hashed password."""
    url = f"https://{okta_domain}/api/v1/users?activate=true"

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"SSWS {api_token}"
    }

    payload = {
        "profile": {
            "firstName": first_name,
            "lastName": last_name,
            "email": username,
            "login": username
        },
        "credentials": {
            "password": {
                "hash": {
                    "algorithm": algorithm,
                    "salt": salt_b64,
                    "saltOrder": "POSTFIX",
                    "value": hash_b64
                }
            }
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    return response


def authenticate_user(okta_domain: str, username: str, password: str) -> dict:
    """Authenticate user using /authn endpoint with clear text password."""
    url = f"https://{okta_domain}/api/v1/authn"

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "username": username,
        "password": password,
        "options": {
            "multiOptionalFactorEnroll": False,
            "warnBeforePasswordExpired": False
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    return response


def get_algorithm_choice() -> str:
    """Prompt user to select hashing algorithm."""
    print("\nSelect hashing algorithm:")
    print("1. SHA-1")
    print("2. SHA-256")
    print("3. SHA-512")

    while True:
        choice = input("\nEnter your choice (1-3): ").strip()
        if choice == "1":
            return "SHA-1"
        elif choice == "2":
            return "SHA-256"
        elif choice == "3":
            return "SHA-512"
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")


def main():
    print("=" * 60)
    print("Okta User Creation with Hashed Password")
    print("=" * 60)

    # Get Okta configuration from environment variables
    okta_domain = os.environ.get("OKTA_DOMAIN")
    api_token = os.environ.get("OKTA_API_TOKEN")

    if not okta_domain or not api_token:
        print("\nError: Missing required environment variables.")
        print("Please set:")
        print("  - OKTA_DOMAIN (e.g., dev-123456.okta.com)")
        print("  - OKTA_API_TOKEN (your Okta API token)")
        sys.exit(1)

    # Get user input
    print(f"\nOkta Domain: {okta_domain}")

    username = input("\nEnter username (email format): ").strip()
    if not username or "@" not in username:
        print("Error: Invalid username. Must be in email format.")
        sys.exit(1)

    first_name = input("Enter first name: ").strip()
    last_name = input("Enter last name: ").strip()

    if not first_name or not last_name:
        print("Error: First name and last name are required.")
        sys.exit(1)

    # Get algorithm choice
    algorithm = get_algorithm_choice()

    # Generate random password and salt
    password = generate_random_password(16)
    salt = generate_random_salt(16)

    print("\n" + "-" * 60)
    print("Generated Credentials")
    print("-" * 60)
    print(f"Password (clear text): {password}")
    print(f"Algorithm: {algorithm}")
    print(f"Salt (base64): {base64.b64encode(salt).decode('utf-8')}")

    # Hash the password
    password_hash = hash_password(password, salt, algorithm)
    salt_b64 = base64.b64encode(salt).decode('utf-8')
    hash_b64 = base64.b64encode(password_hash).decode('utf-8')

    print(f"Hash (base64): {hash_b64}")

    # Create user in Okta
    print("\n" + "-" * 60)
    print("Creating User in Okta")
    print("-" * 60)

    response = create_okta_user(
        okta_domain, api_token, username,
        first_name, last_name,
        algorithm, salt_b64, hash_b64
    )

    if response.status_code == 200:
        user_data = response.json()
        print(f"User created successfully!")
        print(f"User ID: {user_data.get('id')}")
        print(f"Status: {user_data.get('status')}")
    else:
        print(f"Error creating user: {response.status_code}")
        print(f"Response: {response.text}")
        sys.exit(1)

    # Validate credentials using /authn
    print("\n" + "-" * 60)
    print("Validating Credentials via /authn")
    print("-" * 60)

    auth_response = authenticate_user(okta_domain, username, password)

    if auth_response.status_code == 200:
        auth_data = auth_response.json()
        print(f"Authentication successful!")
        print(f"Status: {auth_data.get('status')}")
        if auth_data.get('sessionToken'):
            print(f"Session Token: {auth_data.get('sessionToken')[:20]}...")
    else:
        print(f"Authentication failed: {auth_response.status_code}")
        print(f"Response: {auth_response.text}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Username: {username}")
    print(f"Password: {password}")
    print(f"Algorithm: {algorithm}")
    print("User created and authenticated successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
