from enum import Enum
from typing import Union

from gen_ai_hub.orchestration.models.base import JSONSerializable


class ContentFilterProvider(str, Enum):
    """
    Enumerates supported content filter providers.

    This enum defines the available content filtering services that can be used
    for content moderation tasks. Each enum value represents a specific provider.

    Values:
        AZURE: Represents the Azure Content Safety service.
        LLAMA_GUARD_3_8B: Represents the Llama Guard 3 based on Llama-3.1-8B pretrained model.
    """

    AZURE = "azure_content_safety"
    LLAMA_GUARD_3_8B = "llama_guard_3_8b"


class ContentFilter(JSONSerializable):
    """
    Base class for content filtering configurations.

    This class provides a generic structure for defining content filters
    from various providers. It allows for specifying the provider and
    associated configuration parameters.

    Args:
        provider: The name of the content filter provider.
        config: A dictionary containing the configuration parameters for the content filter.
    """

    def __init__(self, provider: Union[ContentFilterProvider, str], config: dict):
        self.provider = provider
        self.config = config

    def to_dict(self):
        return {"type": self.provider, "config": self.config}

