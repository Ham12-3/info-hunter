"""
AI Provider Adapter - Unified interface for OpenAI and Anthropic.
Provides abstraction for switching between providers easily.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None, 
                          temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """Generate text completion from prompt."""
        pass
    
    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and available."""
        pass


class OpenAIProvider(AIProvider):
    """OpenAI provider implementation."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.openai_api_key
        self._client = None
    
    def _get_client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            try:
                import openai
                if not self.api_key:
                    raise ValueError("OpenAI API key not configured")
                self._client = openai.AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError("openai package not installed. Install with: pip install openai")
        return self._client
    
    def is_available(self) -> bool:
        """Check if OpenAI is configured."""
        return self.api_key is not None
    
    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None,
                          temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """Generate text using OpenAI API."""
        if not self.is_available():
            raise ValueError("OpenAI API key not configured")
        
        client = self._get_client()
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",  # Cost-effective model
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"}  # Enforce JSON output
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI text-embedding-3-small."""
        if not self.is_available():
            raise ValueError("OpenAI API key not configured")
        
        client = self._get_client()
        
        try:
            response = await client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            raise


class AnthropicProvider(AIProvider):
    """Anthropic provider implementation."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.anthropic_api_key
        self._client = None
        # Anthropic doesn't have native embeddings, so we'll use OpenAI for embeddings
        self._embedding_provider = None
    
    def _get_client(self):
        """Lazy initialization of Anthropic client."""
        if self._client is None:
            try:
                import anthropic
                if not self.api_key:
                    raise ValueError("Anthropic API key not configured")
                self._client = anthropic.AsyncAnthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError("anthropic package not installed. Install with: pip install anthropic")
        return self._client
    
    def _get_embedding_provider(self):
        """Get OpenAI provider for embeddings (Anthropic doesn't provide embeddings)."""
        if self._embedding_provider is None:
            self._embedding_provider = OpenAIProvider()
        return self._embedding_provider
    
    def is_available(self) -> bool:
        """Check if Anthropic is configured."""
        return self.api_key is not None
    
    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None,
                          temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """Generate text using Anthropic API."""
        if not self.is_available():
            raise ValueError("Anthropic API key not configured")
        
        client = self._get_client()
        
        try:
            message = await client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt or "",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            # Anthropic returns text blocks
            content = message.content
            if isinstance(content, list) and len(content) > 0:
                if hasattr(content[0], 'text'):
                    return content[0].text
                elif isinstance(content[0], dict):
                    return content[0].get('text', '')
            return str(content)
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI (Anthropic doesn't provide embeddings)."""
        # Use OpenAI for embeddings when using Anthropic as primary provider
        embedding_provider = self._get_embedding_provider()
        if not embedding_provider.is_available():
            raise ValueError("OpenAI API key required for embeddings when using Anthropic")
        return await embedding_provider.generate_embedding(text)


def get_ai_provider() -> AIProvider:
    """
    Factory function to get the configured AI provider.
    Returns the provider instance based on settings.
    """
    provider_name = settings.ai_provider.lower()
    
    if provider_name == "anthropic":
        provider = AnthropicProvider()
        if provider.is_available():
            return provider
        logger.warning("Anthropic not available, falling back to OpenAI")
    
    # Default to OpenAI
    provider = OpenAIProvider()
    if not provider.is_available():
        logger.warning("No AI provider configured. AI features will be disabled.")
    
    return provider

