# Compatibility shim — module moved to ollama.pipelines.tool_executor
from ollama.pipelines.tool_executor import *  # noqa: F401,F403
from ollama.pipelines.tool_executor import _register_default_tools  # noqa: F401
