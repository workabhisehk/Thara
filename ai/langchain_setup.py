"""
LangChain setup for AI agent.
"""
import logging
from langchain.memory import ConversationSummaryMemory, ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from config import settings

logger = logging.getLogger(__name__)

# Initialize LLM
llm = None
fallback_llm = None


def get_llm():
    """Get primary LLM (Gemini)."""
    global llm
    if llm is None:
        try:
            llm = ChatGoogleGenerativeAI(
                model="gemini-pro",
                google_api_key=settings.gemini_api_key,
                temperature=0.7
            )
            logger.info("Gemini LLM initialized")
        except Exception as e:
            logger.error(f"Error initializing Gemini: {e}")
            raise
    return llm


def get_fallback_llm():
    """Get fallback LLM (OpenAI)."""
    global fallback_llm
    if fallback_llm is None and settings.openai_api_key:
        try:
            fallback_llm = ChatOpenAI(
                model="gpt-4",
                api_key=settings.openai_api_key,
                temperature=0.7
            )
            logger.info("OpenAI fallback LLM initialized")
        except Exception as e:
            logger.error(f"Error initializing OpenAI: {e}")
    return fallback_llm


def get_memory():
    """Get conversation memory."""
    # Use summary memory for long-term context
    return ConversationSummaryMemory(
        llm=get_llm(),
        return_messages=True,
        memory_key="chat_history"
    )


def get_buffer_memory():
    """Get buffer memory for recent context."""
    return ConversationBufferMemory(
        return_messages=True,
        memory_key="chat_history"
    )

