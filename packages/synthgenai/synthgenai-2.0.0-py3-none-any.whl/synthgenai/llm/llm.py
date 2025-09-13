"""LLM module"""

import os
from typing import Dict, List, Union

import litellm
from litellm import (
    acompletion,
    completion,
    get_supported_openai_params,
    supports_response_schema,
)
from loguru import logger
from pydantic import BaseModel

from synthgenai.llm.base_llm import BaseLLM
from synthgenai.schemas.config import LLMConfig
from synthgenai.schemas.messages import InputMessage

ALLOWED_PREFIXES = [
    "groq/",
    "mistral/",
    "gemini/",
    "bedrock/",
    "sagemaker/",
    "claude",
    "gpt",
    "huggingface/",
    "ollama/",
    "hosted_vllm/",
    "azure/",
    "azure_ai/",
    "vertex_ai/",
    "deepseek/",
    "xai/",
    "openrouter/",
]


class LLM(BaseLLM):
    """LLM Class"""

    def __init__(self, llm_config: LLMConfig):
        """
        Initialize the LLM class

        Args:
            llm_config (LLMConfig): The configuration for the LLM
        """
        super().__init__(llm_config)

        self._check_allowed_models()
        if self.api_key is None:
            self._check_llm_api_keys()
        self._check_langfuse_api_keys()
        self._check_vllm()
        self._check_ollama()

        logger.info(
            f"Initialized LLM model for synthetic dataset creation: {self.model}"
        )

    def _check_allowed_models(self) -> None:
        """Check if the model is allowed"""
        if not any(self.model.startswith(prefix) for prefix in ALLOWED_PREFIXES):
            logger.error(f"Model {self.model} is not allowed")
            raise ValueError(f"Model {self.model} is not allowed")

    def _check_llm_api_keys(self) -> None:
        """Check if the required API keys are set"""
        api_key_checks = {
            "groq": "GROQ_API_KEY",
            "mistral": "MISTRAL_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "bedrock": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION"],
            "sagemaker": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION"],
            "claude": "ANTHROPIC_API_KEY",
            "gpt": "OPENAI_API_KEY",
            "huggingface": "HUGGINGFACE_API_KEY",
            "azure": ["AZURE_API_KEY", "AZURE_API_BASE", "AZURE_API_VERSION"],
            "azure_ai": ["AZURE_AI_API_KEY", "AZURE_AI_API_BASE"],
            "vertex_ai": [
                "GOOGLE_APPLICATION_CREDENTIALS",
                "VERTEXAI_LOCATION",
                "VERTEXAI_PROJECT",
            ],
            "deepseek": "DEEPSEEK_API_KEY",
            "xai": "XAI_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
        }

        for key, env_vars in api_key_checks.items():
            if self.model.startswith(key):
                if isinstance(env_vars, List):
                    missing_vars = [
                        var for var in env_vars if os.environ.get(var) is None
                    ]
                    if missing_vars:
                        if key == "bedrock" or key == "sagemaker":
                            if all(
                                os.environ.get(var)
                                for var in [
                                    "AWS_ACCESS_KEY_ID",
                                    "AWS_SECRET_ACCESS_KEY",
                                    "AWS_REGION",
                                ]
                            ):
                                logger.info(
                                    "AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_REGION are set"
                                )
                            elif all(
                                os.environ.get(var)
                                for var in ["AWS_REGION", "AWS_PROFILE"]
                            ):
                                logger.info(
                                    "AWS_REGION and AWS_PROFILE are set, using them for bedrock model"
                                )
                            else:
                                for var in missing_vars:
                                    logger.error(f"{var} is not set")
                                raise ValueError(
                                    f"{', '.join(missing_vars)} are not set"
                                )
                        elif key == "azure":
                            if all(
                                os.environ.get(var)
                                for var in [
                                    "AZURE_API_KEY",
                                    "AZURE_API_BASE",
                                    "AZURE_API_VERSION",
                                ]
                            ):
                                logger.info(
                                    "AZURE_API_KEY, AZURE_API_BASE, and AZURE_API_VERSION are set"
                                )
                            elif all(
                                os.environ.get(var)
                                for var in ["AZURE_AD_TOKEN", "AZURE_API_TYPE"]
                            ):
                                logger.info(
                                    "AZURE_AD_TOKEN and AZURE_API_TYPE are set, using them for azure model"
                                )
                            else:
                                for var in missing_vars:
                                    logger.error(f"{var} is not set")
                                raise ValueError(
                                    f"{', '.join(missing_vars)} are not set"
                                )
                        else:
                            for var in missing_vars:
                                logger.error(f"{var} is not set")
                            raise ValueError(f"{', '.join(missing_vars)} are not set")
                else:
                    if os.environ.get(env_vars) is None:
                        logger.error(f"{env_vars} is not set")
                        raise ValueError(f"{env_vars} is not set")
        logger.info("Necessary LLM API Keys are set")

    def _check_langfuse_api_keys(self) -> None:
        """Check if the required API keys for Langfuse are set"""
        if "LANGFUSE_PUBLIC_KEY" in os.environ and "LANGFUSE_SECRET_KEY" in os.environ:
            if "LANGFUSE_OTEL_HOST" in os.environ:
                litellm.callbacks = ["langfuse_otel"]
                logger.info("Langfuse OTEL API keys are set")
            elif "LANGFUSE_HOST" in os.environ:
                litellm.callbacks = ["langfuse"]
                litellm.failure_callback = ["langfuse"]
                logger.info("Langfuse API keys are set")
            else:
                logger.warning(
                    "Langfuse API keys are set but LANGFUSE_HOST or LANGFUSE_OTEL_HOST is not set"
                )
        else:
            logger.warning("Langfuse API keys are not set")

    def _check_vllm(self) -> None:
        """Check if the model is a VLLM model"""
        if self.model.startswith("hosted_vllm") and self.api_base is None:
            logger.error("VLLM model detected without API Base")
            raise ValueError("VLLM model detected without API Base")

    def _check_ollama(self) -> None:
        """Check if the model is an Ollama model"""
        if self.model.startswith("ollama") and self.api_base is None:
            self.api_base = "http://localhost:11434"
            logger.info(
                "Ollama model detected without API Base - setting API Base to localhost"
            )

    def set_temperature(self, temperature: Union[float, None]) -> None:
        """
        Set the temperature for the LLM

        Args:
            temperature (Union[float, None]): The temperature to set
        """
        self.temperature = temperature

    def get_temperature(self) -> Union[float, None]:
        """
        Get the temperature for the LLM

        Returns:
            Union[float, None]: The temperature if set, None otherwise
        """
        return self.temperature

    def get_model(self) -> str:
        """
        Get the model name

        Returns:
            str: The model name
        """
        return self.model

    def set_response_format(
        self, response_format: Union[Dict, BaseModel, type[BaseModel]]
    ) -> None:
        """
        Set the response format for the LLM

        Args:
            response_format (Union[dict, BaseModel, type[BaseModel]]):
                The response format to set
        """
        self.response_format = response_format

    def check_response_format(self) -> bool:
        """
        Check if the response format is supported by the LLM model

        Returns:
            bool: True if the response format is supported, False otherwise
        """
        if self.model.startswith("gpt") or self.model.startswith("claude"):
            custom_llm_provider = None
        else:
            custom_llm_provider = self.model.split("/")[0]

        supported_params = get_supported_openai_params(
            model=self.model, custom_llm_provider=custom_llm_provider
        )
        if (
            supported_params is not None
            and "response_format" in supported_params
            and supports_response_schema(
                model=self.model, custom_llm_provider=custom_llm_provider
            )
        ):
            return True
        else:
            logger.warning(
                f"JSON format is not supported by the LLM model: {self.model}"
            )
            return False

    def generate(self, messages: List[InputMessage]) -> str:
        """
        Generate completions using the LLM API

        Args:
            messages (List[InputMessage]): List of messages to generate
                completions for using the LLM API

        Returns:
            str: The completion generated by the LLM API
        """
        try:
            logger.info(f"Generating completion with model: {self.model}")
            logger.debug(f"Messages: {messages}")
            response = completion(
                model=self.model,
                messages=messages,
                response_format=self.response_format,
                temperature=self.temperature,
                top_p=self.top_p,
                max_tokens=self.max_tokens,
                api_base=self.api_base,
                api_key=self.api_key,
                timeout=120,
            )
            logger.info(f"Successfully generated completion using model: {self.model}")
            model_response = response.choices[0].message.content

            return model_response
        except Exception as e:
            logger.error(f"Failed to generate completions with model {self.model}: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            raise

    async def agenerate(self, messages: List[InputMessage]) -> str:
        """
        Generate completions using the LLM API asynchronously.

        Args:
            messages (List[InputMessage]): List of messages to generate
                completions for using the LLM API

        Returns:
            str: The completion generated by the LLM API.
        """
        try:
            logger.info(f"Async generating completion with model: {self.model}")
            logger.debug(f"Messages: {messages}")
            response = await acompletion(
                model=self.model,
                messages=messages,
                response_format=self.response_format,
                temperature=self.temperature,
                top_p=self.top_p,
                max_tokens=self.max_tokens,
                api_base=self.api_base,
                api_key=self.api_key,
                timeout=120,
            )
            model_response = response.choices[0].message.content
            logger.info(f"Successfully generated async completion using: {self.model}")

            return model_response
        except Exception as e:
            logger.error(f"Failed to generate async completions with {self.model}: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            raise
