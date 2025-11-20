"""
Google Calendar OAuth2 authentication.
"""
import logging
from typing import Optional, Dict, Any
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from config import settings
from database.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# OAuth2 scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']


def get_authorization_url(user_id: int) -> str:
    """
    Get Google OAuth2 authorization URL.
    
    Args:
        user_id: User ID
    
    Returns:
        Authorization URL
    """
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.google_redirect_uri]
            }
        },
        scopes=SCOPES
    )
    flow.redirect_uri = settings.google_redirect_uri
    
    authorization_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        state=str(user_id)  # Store user_id in state
    )
    
    return authorization_url


async def handle_oauth_callback(
    session: AsyncSession,
    authorization_code: str,
    user_id: int
) -> bool:
    """
    Handle OAuth2 callback and store credentials.
    
    Args:
        session: Database session
        authorization_code: Authorization code from callback
        user_id: User ID
    
    Returns:
        True if successful
    """
    try:
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.google_redirect_uri]
                }
            },
            scopes=SCOPES
        )
        flow.redirect_uri = settings.google_redirect_uri
        
        # Exchange code for token
        flow.fetch_token(code=authorization_code)
        credentials = flow.credentials
        
        # Store credentials in database
        stmt = update(User).where(
            User.id == user_id
        ).values(
            google_calendar_connected=True,
            google_access_token=credentials.token,
            google_refresh_token=credentials.refresh_token,
            google_token_expires_at=datetime.utcnow() + timedelta(seconds=credentials.expiry)
        )
        
        await session.execute(stmt)
        await session.commit()
        
        logger.info(f"Google Calendar connected for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error handling OAuth callback: {e}")
        return False


async def get_user_credentials(session: AsyncSession, user_id: int) -> Optional[Credentials]:
    """
    Get valid credentials for user.
    
    Args:
        session: Database session
        user_id: User ID
    
    Returns:
        Credentials object or None
    """
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or not user.google_calendar_connected:
        return None
    
    # Create credentials object
    creds = Credentials(
        token=user.google_access_token,
        refresh_token=user.google_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=SCOPES
    )
    
    # Refresh if expired
    if user.google_token_expires_at and user.google_token_expires_at <= datetime.utcnow():
        try:
            creds.refresh(Request())
            
            # Update in database
            stmt = update(User).where(
                User.id == user_id
            ).values(
                google_access_token=creds.token,
                google_token_expires_at=datetime.utcnow() + timedelta(seconds=creds.expiry)
            )
            await session.execute(stmt)
            await session.commit()
            
        except Exception as e:
            logger.error(f"Error refreshing credentials: {e}")
            return None
    
    return creds


def get_calendar_service(credentials: Credentials):
    """
    Get Google Calendar service.
    
    Args:
        credentials: OAuth2 credentials
    
    Returns:
        Calendar service object
    """
    return build('calendar', 'v3', credentials=credentials)

