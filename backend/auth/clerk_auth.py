"""
Clerk JWT authentication for FastAPI
"""
import requests
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import os
from dotenv import load_dotenv
from jose import jwt, JWTError

load_dotenv()

CLERK_JWKS_URL = "https://promoted-octopus-95.clerk.accounts.dev/.well-known/jwks.json"

security = HTTPBearer()


def get_clerk_jwks():
    """Fetch Clerk's JWKS"""
    try:
        response = requests.get(CLERK_JWKS_URL)
        return response.json()
    except Exception as e:
        print(f"Error fetching JWKS: {e}")
        return None


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """
    Verify Clerk JWT token and return user data
    """
    token = credentials.credentials
    
    try:
        jwks = get_clerk_jwks()
        if not jwks:
            raise HTTPException(status_code=500, detail="Could not fetch public keys")
        
        unverified_header = jwt.get_unverified_header(token)
        
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = key
                break
        
        if not rsa_key:
            raise HTTPException(status_code=401, detail="Invalid token: Key not found")
        
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            options={"verify_signature": True}
        )
        
        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
        }
        
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication error: {str(e)}")


def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """
    FastAPI dependency to get current authenticated user
    """
    return verify_token(credentials)
