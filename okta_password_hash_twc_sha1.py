#!/usr/bin/env python3
"""
Okta SHA-1 User Management and Authentication

This script:
1. Deletes users if they already exist in Okta
2. Creates users with SHA-1 hashed passwords
3. Authenticates users via /authn with clear text password

Required environment variables in .env:
- OKTA_DOMAIN: Your Okta domain
- OKTA_API_TOKEN: Your Okta API token
- USER1_USERNAME, USER1_PASSWORD, USER1_HASH, USER1_SALT, USER1_FIRSTNAME, USER1_LASTNAME
- USER2_USERNAME, USER2_PASSWORD, USER2_HASH, USER2_SALT, USER2_FIRSTNAME, USER2_LASTNAME
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_headers(api_token: str) -> dict:
    """Return common headers for Okta API calls."""
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"SSWS {api_token}"
    }


def find_user_by_login(okta_domain: str, api_token: str, username: str) -> dict | None:
    """Search for a user by login/email. Returns user object if found, None otherwise."""
    url = f"https://{okta_domain}/api/v1/users?q={username}&limit=1"

    response = requests.get(url, headers=get_headers(api_token))

    if response.status_code == 200:
        users = response.json()
        for user in users:
            if user.get('profile', {}).get('login') == username:
                return user
    return None


def delete_user(okta_domain: str, api_token: str, user_id: str, username: str) -> bool:
    """Deactivate and delete a user by ID."""
    headers = get_headers(api_token)

    # First deactivate the user
    deactivate_url = f"https://{okta_domain}/api/v1/users/{user_id}/lifecycle/deactivate"
    deactivate_response = requests.post(deactivate_url, headers=headers)

    if deactivate_response.status_code not in [200, 204]:
        # User might already be deactivated, continue to delete
        pass

    # Then delete the user
    delete_url = f"https://{okta_domain}/api/v1/users/{user_id}"
    delete_response = requests.delete(delete_url, headers=headers)

    if delete_response.status_code in [200, 204]:
        print(f"  Deleted user: {username} (ID: {user_id})")
        return True
    else:
        print(f"  Failed to delete user: {delete_response.status_code}")
        print(f"  Response: {delete_response.text}")
        return False


def create_user_with_hash(okta_domain: str, api_token: str, username: str,
                          first_name: str, last_name: str,
                          salt_b64: str, hash_b64: str) -> dict:
    """Create a user in Okta with a SHA-1 hashed password."""
    url = f"https://{okta_domain}/api/v1/users?activate=true"

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
                    "algorithm": "SHA-1",
                    "salt": salt_b64,
                    "saltOrder": "POSTFIX",
                    "value": hash_b64
                }
            }
        }
    }

    response = requests.post(url, headers=get_headers(api_token), json=payload)
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


def load_user_credentials():
    """Load user credentials from environment variables."""
    users = []

    # User 1
    user1_username = os.environ.get("USER1_USERNAME")
    user1_password = os.environ.get("USER1_PASSWORD")
    user1_hash = os.environ.get("USER1_HASH")
    user1_salt = os.environ.get("USER1_SALT")
    user1_firstname = os.environ.get("USER1_FIRSTNAME", "User")
    user1_lastname = os.environ.get("USER1_LASTNAME", "One")

    if user1_username:
        # Check if salt is provided and not a placeholder
        has_salt = bool(user1_salt and not user1_salt.startswith("base64Encoded"))
        users.append({
            "username": user1_username,
            "password": user1_password or "",
            "hash": user1_hash or "",
            "salt": user1_salt or "",
            "firstname": user1_firstname,
            "lastname": user1_lastname,
            "has_salt": has_salt
        })

    # User 2
    user2_username = os.environ.get("USER2_USERNAME")
    user2_password = os.environ.get("USER2_PASSWORD")
    user2_hash = os.environ.get("USER2_HASH")
    user2_salt = os.environ.get("USER2_SALT")
    user2_firstname = os.environ.get("USER2_FIRSTNAME", "User")
    user2_lastname = os.environ.get("USER2_LASTNAME", "Two")

    if user2_username:
        # Check if salt is provided and not a placeholder
        has_salt = bool(user2_salt and not user2_salt.startswith("base64Encoded"))
        users.append({
            "username": user2_username,
            "password": user2_password or "",
            "hash": user2_hash or "",
            "salt": user2_salt or "",
            "firstname": user2_firstname,
            "lastname": user2_lastname,
            "has_salt": has_salt
        })

    return users


def main():
    print("=" * 60)
    print("Okta SHA-1 User Management and Authentication")
    print("=" * 60)

    # Get Okta configuration from environment variables
    okta_domain = os.environ.get("OKTA_DOMAIN")
    api_token = os.environ.get("OKTA_API_TOKEN")

    if not okta_domain or not api_token:
        print("\nError: Missing OKTA_DOMAIN or OKTA_API_TOKEN in .env file.")
        sys.exit(1)

    print(f"\nOkta Domain: {okta_domain}")

    # Load user credentials from .env
    users = load_user_credentials()

    if not users:
        print("\nError: No user credentials found in .env file.")
        print("Please configure USER1_* and/or USER2_* variables.")
        print("Required: USERNAME, PASSWORD, HASH, SALT")
        sys.exit(1)

    # Separate users with and without salt
    users_with_salt = [u for u in users if u['has_salt']]
    users_without_salt = [u for u in users if not u['has_salt']]

    print(f"Found {len(users)} user(s) in .env file.")
    print(f"  - {len(users_with_salt)} user(s) with salt (will be processed)")
    print(f"  - {len(users_without_salt)} user(s) without salt (will be skipped)")

    if users_without_salt:
        print("\nSkipping users without salt:")
        for user in users_without_salt:
            print(f"  - {user['username']}")

    if not users_with_salt:
        print("\nError: No users with valid salt found. Nothing to process.")
        sys.exit(1)

    print()

    # Step 1: Delete existing users
    print("=" * 60)
    print("Step 1: Checking and Deleting Existing Users")
    print("=" * 60)

    for user in users_with_salt:
        print(f"\nChecking if user exists: {user['username']}")
        existing_user = find_user_by_login(okta_domain, api_token, user['username'])

        if existing_user:
            user_id = existing_user.get('id')
            print(f"  User found with ID: {user_id}")
            delete_user(okta_domain, api_token, user_id, user['username'])
        else:
            print(f"  User does not exist, skipping delete.")

    # Step 2: Create users with hashed passwords
    print("\n" + "=" * 60)
    print("Step 2: Creating Users with SHA-1 Hashed Passwords")
    print("=" * 60)

    created_users = []
    for user in users_with_salt:
        print(f"\nCreating user: {user['username']}")
        print(f"  Name: {user['firstname']} {user['lastname']}")
        print(f"  Salt (base64): {user['salt']}")
        print(f"  Hash (base64): {user['hash']}")

        response = create_user_with_hash(
            okta_domain, api_token,
            user['username'],
            user['firstname'], user['lastname'],
            user['salt'], user['hash']
        )

        if response.status_code == 200:
            user_data = response.json()
            print(f"  Created successfully!")
            print(f"  User ID: {user_data.get('id')}")
            print(f"  Status: {user_data.get('status')}")
            created_users.append(user)
        else:
            print(f"  Failed to create user: {response.status_code}")
            print(f"  Response: {response.text}")

    # Step 3: Authenticate users
    print("\n" + "=" * 60)
    print("Step 3: Authenticating Users via /authn")
    print("=" * 60)

    results = []
    for user in created_users:
        print(f"\nAuthenticating: {user['username']}")
        print(f"  Password: {user['password']}")

        response = authenticate_user(okta_domain, user['username'], user['password'])

        if response.status_code == 200:
            auth_data = response.json()
            status = auth_data.get('status')
            print(f"  Result: SUCCESS")
            print(f"  Status: {status}")
            if auth_data.get('sessionToken'):
                print(f"  Session Token: {auth_data.get('sessionToken')[:20]}...")
            results.append({"user": user['username'], "success": True, "status": status})
        else:
            print(f"  Result: FAILED")
            print(f"  HTTP Status: {response.status_code}")
            try:
                error_data = response.json()
                print(f"  Error: {error_data.get('errorSummary', 'Unknown error')}")
            except:
                print(f"  Response: {response.text}")
            results.append({"user": user['username'], "success": False, "status": "FAILED"})

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    # Show skipped users
    for user in users_without_salt:
        print(f"[SKIP] {user['username']} - No salt provided")

    # Show processed users
    for result in results:
        status_icon = "OK" if result['success'] else "FAIL"
        print(f"[{status_icon}] {result['user']} - {result['status']}")

    print("=" * 60)

    # Exit with error if any authentication failed
    if results and not all(r['success'] for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
