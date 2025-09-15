"""
Monkey Coder SDK - Python client

A comprehensive client library that provides:
- Authentication and token management
- Automatic retries with exponential backoff
- Streaming support for real-time execution
- Type-safe interfaces for all API endpoints
- Error handling and request/response transformation
"""

from .client import MonkeyCoderClient, MonkeyCoderError
from .types import (
    TaskType,
    PersonaType,
    ProviderType,
    TaskStatus,
    ExecutionContext,
    PersonaConfig,
    Monkey1Config,
    OrchestrationConfig,
    ExecuteRequest,
    ExecuteResponse,
    StreamEvent,
    UsageRequest,
    HealthResponse,
    MonkeyCoderClientConfig,
    # Backward compatibility aliases
    SuperClaudeConfig,
    Gary8DConfig,
)
from .helpers import (
    create_execute_request,
    create_code_generation_request,
    create_code_review_request,
)

__version__ = "1.0.0"
__all__ = [
    "MonkeyCoderClient",
    "MonkeyCoderError",
    "TaskType",
    "PersonaType", 
    "ProviderType",
    "TaskStatus",
    "ExecutionContext",
    "PersonaConfig",
    "Monkey1Config",
    "OrchestrationConfig",
    "ExecuteRequest",
    "ExecuteResponse",
    "StreamEvent",
    "UsageRequest",
    "HealthResponse",
    "MonkeyCoderClientConfig",
    "create_execute_request",
    "create_code_generation_request",
    "create_code_review_request",
    # Backward compatibility aliases
    "SuperClaudeConfig",
    "Gary8DConfig",
]
