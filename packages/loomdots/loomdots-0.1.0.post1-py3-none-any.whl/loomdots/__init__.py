# Universal A2A Adapter: Main API
from .expose import (
    expose,
    run,
    expose_function,
    expose_process, 
    expose_container,
    get_registered_agents,
    unregister_agent,
    clear_registry,
    configure_security,
    ExpositionError,
    SecurityViolationError,
    ResourceLimitError,
)

# Advanced components for power users
from .introspection import (
    infer_agent_metadata,
    infer_capabilities,
    infer_skills,
    IntrospectionError,
    SecurityError as IntrospectionSecurityError,
)

from .validation import (
    validate_agent_config,
    ValidationError,
    SecurityValidationError,
    check_system_resources,
)

from .wrappers import (
    ProcessWrapper,
    ContainerWrapper, 
    SecurityWrapper,
    WrapperError,
    SecurityWrapperError,
    ResourceLimitExceededError,
)

__all__ = [
    # Primary interface - dead simple for developers
    "expose",
    "run",
    # Convenience functions (optional, same as expose)
    "expose_function",
    "expose_process",
    "expose_container",
    # Agent management
    "get_registered_agents",
    "unregister_agent",
    "clear_registry", 
    "configure_security",
    # Exceptions (users shouldn't normally need to import these)
    "ExpositionError",
    "SecurityViolationError",
    "ResourceLimitError",
    # Advanced/Internal APIs (for framework builders and power users)
    "ValidationError",
    "SecurityValidationError", 
    "IntrospectionError",
    "IntrospectionSecurityError",
    "WrapperError",
    "SecurityWrapperError",
    "ResourceLimitExceededError",
    "infer_agent_metadata",
    "infer_capabilities",
    "infer_skills", 
    "validate_agent_config",
    "check_system_resources",
    "ProcessWrapper",
    "ContainerWrapper",
    "SecurityWrapper",
]
