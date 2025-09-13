"""
Configuration presets for popular OpenAI-compatible inference providers.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ProviderConfig:
    """Configuration for an inference provider."""
    base_url: str
    default_model: str
    api_key_env: str
    headers: Optional[Dict[str, str]] = None
    query_params: Optional[Dict[str, str]] = None
    description: str = ""


class InferenceProviders:
    """Predefined configurations for popular inference providers."""
    
    OPENAI = ProviderConfig(
        base_url="https://api.openai.com/v1",
        default_model="gpt-3.5-turbo",
        api_key_env="OPENAI_API_KEY",
        description="Official OpenAI API"
    )
    
    LOCAL_TEXTGEN = ProviderConfig(
        base_url="http://localhost:5000/v1",
        default_model="local-model",
        api_key_env="LOCAL_API_KEY",
        description="text-generation-webui server"
    )
    
    LOCAL_VLLM = ProviderConfig(
        base_url="http://localhost:8000/v1",
        default_model="local-model",
        api_key_env="VLLM_API_KEY",
        description="vLLM inference server"
    )
    
    OLLAMA = ProviderConfig(
        base_url="http://localhost:11434/v1",
        default_model="llama2",
        api_key_env="OLLAMA_API_KEY",
        description="Ollama local inference"
    )
    
    TOGETHER = ProviderConfig(
        base_url="https://api.together.xyz/v1",
        default_model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        api_key_env="TOGETHER_API_KEY",
        description="Together AI platform"
    )
    
    ANYSCALE = ProviderConfig(
        base_url="https://api.endpoints.anyscale.com/v1",
        default_model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        api_key_env="ANYSCALE_API_KEY",
        description="Anyscale Endpoints"
    )
    
    PERPLEXITY = ProviderConfig(
        base_url="https://api.perplexity.ai",
        default_model="llama-3.1-sonar-small-128k-online",
        api_key_env="PERPLEXITY_API_KEY",
        description="Perplexity AI"
    )
    
    GROQ = ProviderConfig(
        base_url="https://api.groq.com/openai/v1",
        default_model="mixtral-8x7b-32768",
        api_key_env="GROQ_API_KEY",
        description="Groq fast inference"
    )
    
    DEEPINFRA = ProviderConfig(
        base_url="https://api.deepinfra.com/v1/openai",
        default_model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        api_key_env="DEEPINFRA_API_KEY",
        description="DeepInfra inference"
    )
    
    @classmethod
    def get_azure_config(cls, 
                        endpoint: str, 
                        deployment_name: str,
                        api_version: str = "2023-12-01-preview") -> ProviderConfig:
        """Generate Azure OpenAI configuration."""
        return ProviderConfig(
            base_url=f"{endpoint}/openai/deployments/{deployment_name}",
            default_model=deployment_name,
            api_key_env="AZURE_OPENAI_KEY",
            headers={"api-key": ""},  # Will be filled from env
            query_params={"api-version": api_version},
            description="Azure OpenAI Service"
        )
    
    @classmethod
    def list_providers(cls) -> Dict[str, ProviderConfig]:
        """Get all available provider configurations."""
        providers = {}
        for attr_name in dir(cls):
            if not attr_name.startswith('_') and not callable(getattr(cls, attr_name)):
                attr_value = getattr(cls, attr_name)
                if isinstance(attr_value, ProviderConfig):
                    providers[attr_name.lower()] = attr_value
        return providers


def create_qa_generator_from_provider(provider_name: str, 
                                    api_key: Optional[str] = None,
                                    model: Optional[str] = None,
                                    **kwargs) -> "LLMQAGenerator":
    """
    Create an LLMQAGenerator instance using a predefined provider configuration.
    
    Args:
        provider_name: Name of the provider (e.g., 'ollama', 'together', 'openai')
        api_key: API key (if None, will try to get from environment)
        model: Model name (if None, will use provider's default)
        **kwargs: Additional arguments for LLMQAGenerator
        
    Returns:
        Configured LLMQAGenerator instance
    """
    import os
    from .llm_generator import LLMQAGenerator
    
    providers = InferenceProviders.list_providers()
    
    if provider_name.lower() not in providers:
        available = ", ".join(providers.keys())
        raise ValueError(f"Unknown provider '{provider_name}'. Available: {available}")
    
    config = providers[provider_name.lower()]
    
    # Get API key from parameter or environment
    if api_key is None:
        api_key = os.getenv(config.api_key_env)
        if api_key is None and config.api_key_env != "LOCAL_API_KEY":
            print(f"Warning: No API key found for {provider_name}. Set {config.api_key_env} environment variable.")
            api_key = "dummy-key"  # For local servers that don't need real keys
    
    # Use provided model or default
    model_name = model or config.default_model
    
    # Prepare request arguments
    request_kwargs = {}
    if config.headers:
        headers = config.headers.copy()
        if api_key and "api-key" in headers:
            headers["api-key"] = api_key
        request_kwargs["headers"] = headers
    
    # Note: query_params would be handled differently with direct HTTP requests
    # They could be added to the URL or handled as request parameters
    
    return LLMQAGenerator(
        api_key=api_key,
        model=model_name,
        base_url=config.base_url,
        **request_kwargs,
        **kwargs
    )