#!/usr/bin/env python3
"""
Helper script to fix DATABASE_URL with special characters in password.
"""
from urllib.parse import urlparse, urlunparse, quote
import os

def fix_database_url(url):
    """Fix database URL by encoding special characters in password."""
    parsed = urlparse(url)
    
    if parsed.password:
        # URL encode the password
        encoded_password = quote(parsed.password, safe='')
        
        # Reconstruct URL with encoded password
        netloc = f"{parsed.username}:{encoded_password}@{parsed.hostname}"
        if parsed.port:
            netloc += f":{parsed.port}"
        
        fixed = urlunparse((
            parsed.scheme,
            netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
        return fixed
    return url

if __name__ == "__main__":
    # Read from .env or get from environment
    db_url = os.getenv("DATABASE_URL", "")
    
    if not db_url:
        print("DATABASE_URL not found in environment")
        print("Please set it or provide as argument")
        exit(1)
    
    print("Original URL:")
    print(db_url[:50] + "...")
    print("\nFixed URL (with encoded password):")
    fixed = fix_database_url(db_url)
    print(fixed)
    print("\nCopy this to your .env file as DATABASE_URL")

