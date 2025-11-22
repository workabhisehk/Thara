"""
LangChain setup for AI agent.
Updated for LangChain v0.3+ (Pydantic v2 compatible).
"""
import logging
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from config import settings

logger = logging.getLogger(__name__)

# Initialize LLM
llm = None
fallback_llm = None


def get_llm():
    """Get primary LLM (OpenAI)."""
    global llm
    if llm is None:
        try:
            llm = ChatOpenAI(
                model="gpt-4o-mini",  # Using gpt-4o-mini for cost efficiency, can change to gpt-4 if needed
                api_key=settings.openai_api_key,
                temperature=0.7
            )
            logger.info("OpenAI LLM initialized")
        except Exception as e:
            logger.error(f"Error initializing OpenAI: {e}")
            raise
    return llm


def get_fallback_llm():
    """Get fallback LLM (Gemini)."""
    global fallback_llm
    if fallback_llm is None and settings.gemini_api_key:
        try:
            fallback_llm = ChatGoogleGenerativeAI(
                model="gemini-pro",
                google_api_key=settings.gemini_api_key,
                temperature=0.7
            )
            logger.info("Gemini fallback LLM initialized")
        except Exception as e:
            logger.error(f"Error initializing Gemini: {e}")
    return fallback_llm


# Note: Memory functionality replaced with database-based storage
# We use the conversation store in database instead of LangChain memory
# This avoids dependency issues and gives us more control

