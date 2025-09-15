"""
This module provides the lists of chat and embedding models available in
LiteLLM.

The source of this module is defined in `calliope_jupyter_ai_magics` because that package
needs to be installable without `calliope_jupyter_ai`. Therefore, the source has to be
defined in `calliope_jupyter_ai_magics.model_list` for now.

In the future, we may provide a shared `calliope_jupyter_ai_models` package that provides
the model list, allowing `calliope_jupyter_ai` and `calliope_jupyter_ai_magics` to be mutually
independent.
"""
from calliope_jupyter_ai_magics.model_list import CHAT_MODELS, EMBEDDING_MODELS # type: ignore