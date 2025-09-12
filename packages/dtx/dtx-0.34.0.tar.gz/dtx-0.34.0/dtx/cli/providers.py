from dtx.core.builders.provider_vars import ProviderVarsBuilder
from dtx_models.providers.base import ProviderType
from dtx_models.providers.litellm import LitellmProvider, LitellmProviderConfig
from dtx_models.providers.ollama import OllamaProvider, OllamaProviderConfig
from dtx_models.providers.openai import OpenaiProvider, OpenaiProviderConfig
from dtx_models.providers.groq import GroqProvider, GroqProviderConfig
from dtx_models.providers.anthropic import AnthropicProvider
from dtx_models.providers.mistral import MistralProvider
from dtx_models.providers.gemini import GeminiProvider
from dtx_models.providers.cerebras import CerebrasProvider
from dtx_models.scope import RedTeamScope
from dtx.plugins.providers.dummy.echo import EchoAgent
from dtx.plugins.providers.eliza.agent import ElizaAgent
from dtx.plugins.providers.gradio.agent import GradioAgent
from dtx.plugins.providers.http.agent import HttpAgent
from dtx.plugins.providers.litellm.agent import LitellmAgent
from dtx.plugins.providers.ollama.agent import OllamaAgent
from dtx.plugins.providers.openai.agent import OpenAIAgent
from dtx.plugins.providers.groq.agent import GroqAgent
from dtx.plugins.providers.anthropic.agent import AnthropicAgent
from dtx.plugins.providers.mistral.agent import MistralAgent
from dtx.plugins.providers.gemini.agent import GeminiAgent
from dtx.plugins.providers.cerebras.agent import CerebrasAgent
from dtx_models.providers.anthropic import AnthropicProviderConfig
from dtx_models.providers.mistral import MistralProviderConfig
from dtx_models.providers.gemini import GeminiProviderConfig
from dtx_models.providers.cerebras import CerebrasProviderConfig


class ProviderFactory:
    """
    Factory class responsible for creating provider agent instances
    based on the given provider type and model configuration.
    Supports multiple provider types including OpenAI, Ollama, LiteLLM, HF, etc.
    """

    def __init__(self, load_env_vars=False):
        """
        :param load_env_vars: Flag to indicate if env variables should be loaded
                              into provider configs automatically.
        """
        self._load_env_vars = load_env_vars

    def _build_env_vars(self, scope):
        """
        Extracts environment variable dictionary from scope.
        Only the first environment is considered (if available).

        :param scope: RedTeamScope
        :return: dict of environment variables
        """
        env_vars = {}
        if scope.environments:
            env_vars = next(ProviderVarsBuilder(scope.environments[0]).build(), {})
        return env_vars

    def get_agent(
        self,
        scope: RedTeamScope,
        provider_type: ProviderType,
        url: str = "",
        env_vars: dict = None,
    ):
        """
        Main factory method to return a configured Agent for the requested provider.

        :param scope: RedTeamScope containing prompt, environment, and provider info.
        :param provider_type: Enum value indicating provider type (e.g., OPENAI, OLLAMA).
        :param url: The model name or endpoint identifier for the provider.
        :param env_vars: Optional env var values to apply to provider configs or agents.
        :return: Instantiated and configured Agent
        """
        from dtx.config import globals
        from dtx.plugins.providers.hf.agent import HFAgent

        # Handle local dummy providers
        if provider_type == ProviderType.ECHO:
            return EchoAgent()

        elif provider_type == ProviderType.ELIZA:
            return ElizaAgent(url)

        # Handle HuggingFace inference models
        elif provider_type == ProviderType.HF:
            model = globals.get_llm_models().get_huggingface_model(url)
            return HFAgent(model)

        # Handle external HTTP-based LLM agents
        elif provider_type == ProviderType.HTTP:
            _vars = env_vars if env_vars is not None else self._build_env_vars(scope)
            return HttpAgent(provider=scope.providers[0], vars=_vars)

        # Gradio-hosted models
        elif provider_type == ProviderType.GRADIO:
            _vars = env_vars if env_vars is not None else self._build_env_vars(scope)
            return GradioAgent(provider=scope.providers[0], vars=_vars)

        # Ollama (local LLM runner)
        elif provider_type == ProviderType.OLLAMA:
            config = OllamaProviderConfig(model=url)
            if self._load_env_vars:
                config.load_from_env()  # Load local endpoint from env (if set)
            config.set_env_var_values(env_vars)
            provider = OllamaProvider(config=config)
            return OllamaAgent(provider)

        # OpenAI API (e.g., gpt-4o, gpt-3.5-turbo)
        elif provider_type == ProviderType.OPENAI:
            config = OpenaiProviderConfig(model=url)
            if self._load_env_vars:
                config.load_from_env()  # Load API key & endpoint
            config.set_env_var_values(env_vars)
            provider = OpenaiProvider(config=config)

            prompt_template = scope.prompts[0] if scope.prompts else None
            return OpenAIAgent(provider, prompt_template=prompt_template)

        # LiteLLM gateway (routes to OpenAI, Groq, etc.)
        elif provider_type == ProviderType.LITE_LLM:
            prompt_template = scope.prompts[0] if scope.prompts else None
            config = LitellmProviderConfig(model=url)

            if self._load_env_vars:
                config.load_from_env()  # Determine upstream provider and apply env vars
            config.set_env_var_values(env_vars)

            provider = LitellmProvider(config=config)
            return LitellmAgent(provider, prompt_template=prompt_template)

        # Groq API
        elif provider_type == ProviderType.GROQ:
            config = GroqProviderConfig(model=url)
            if self._load_env_vars:
                config.load_from_env()  # Determine upstream provider and apply env vars
            config.set_env_var_values(env_vars)
            provider = GroqProvider(config=config)
            return GroqAgent(provider)
        
        # Anthropic API
        elif provider_type == ProviderType.ANTHROPIC:
            config = AnthropicProviderConfig(model=url)
            if self._load_env_vars:
                config.load_from_env()   # Loads ANTHROPIC_API_KEY from env
            config.set_env_var_values(env_vars)
            
            provider = AnthropicProvider(config=config)
            return AnthropicAgent(provider)
        
        # Mistral API
        elif provider_type == ProviderType.MISTRAL:
            config = MistralProviderConfig(model=url)
            if self._load_env_vars:
                config.load_from_env()    # Loads MISTRAL_API_KEY from env
            config.set_env_var_values(env_vars)
            provider = MistralProvider(config=config)
            return MistralAgent(provider)
        
        # Gemini API
        elif provider_type == ProviderType.GEMINI:
            config = GeminiProviderConfig(model=url)
            if self._load_env_vars:
                config.load_from_env()    # Loads GEMINI_API_KEY from env
            config.set_env_var_values(env_vars)
            provider = GeminiProvider(config=config)
            return GeminiAgent(provider)
        
        # Cerebras API
        elif provider_type == ProviderType.CEREBRAS:
            config = CerebrasProviderConfig(model=url)
            if self._load_env_vars:
                config.load_from_env()    # Loads CEREBRAS_API_KEY from env
            config.set_env_var_values(env_vars)
            provider = CerebrasProvider(config=config)
            return CerebrasAgent(provider)

        # Fallback for unsupported provider types
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")