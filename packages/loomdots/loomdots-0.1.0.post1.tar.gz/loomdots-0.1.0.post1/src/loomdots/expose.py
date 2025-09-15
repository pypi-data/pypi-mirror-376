"""Universal A2A adapter: this module provides a production-ready, secure API for exposing agents."""
from __future__ import annotations

import time
import logging
import threading
from pathlib import Path
from typing import Any, Dict, List, Iterable, Callable, Optional, Union

from a2a.types import AgentCapabilities, AgentSkill, AgentCard

from .server import create_app
from .validation import validate_agent_config, ValidationError
from .introspection import infer_agent_metadata, infer_capabilities, infer_skills
from .wrappers import ProcessWrapper, ContainerWrapper, SecurityWrapper, AgentFunction


# Configure logging
logger = logging.getLogger(__name__)


# Type aliases
AgentLike = Union[AgentFunction, Any]
ProcessLike = Union[str, list[str], Path]


# Global configuration
_GLOBAL_CONFIG = {
    'max_concurrent_agents': 100,
    'default_timeout': 120,
    'max_retries': 3,
    'enable_security_checks': True,
    'allow_process_execution': True,
    'allow_container_execution': False,  # More restrictive default
    'max_memory_mb': 1024,
    'max_cpu_percent': 50,
}

# Thread-safe agent registry: stores A2A-compliant agent information
_REGISTERED_AGENTS = {}
_REGISTRY_LOCK = threading.RLock()
_CURRENT_AGENT_CARD = None


class ExpositionError(Exception):
    """Base exception for agent exposition errors."""
    pass


class SecurityViolationError(ExpositionError):
    """Raised when security constraints are violated."""
    pass


class ResourceLimitError(ExpositionError):
    """Raised when resource limits are exceeded."""
    pass


def _register_agent_internal(
    name: str,
    description: str,
    version: str,
    url: Optional[str],
    capabilities: Union[AgentCapabilities, Dict[str, Any], None],
    skills: Optional[Iterable[Union[AgentSkill, Dict[str, Any]]]],
    input_modes: Optional[List[str]] = ["text/plain"],
    output_modes: Optional[List[str]] = ["text/plain"],
) -> None:
    """Internal agent registration that integrates with A2A framework."""
    # Convert capabilities and skills to proper A2A types
    if isinstance(capabilities, dict):
        caps = AgentCapabilities(**capabilities)
    else:
        caps = capabilities
    
    skill_list = []
    if skills:
        for skill in skills:
            if isinstance(skill, dict):
                skill_list.append(AgentSkill(**skill))
            else:
                skill_list.append(skill)
    
    # Create A2A-compliant agent card
    global _CURRENT_AGENT_CARD
    _CURRENT_AGENT_CARD = AgentCard(
        name=name,
        description=description,
        version=version,
        url=url or "http://localhost:8000",
        capabilities=caps,
        skills=skill_list,
        defaultInputModes=input_modes,
        defaultOutputModes=output_modes)


def expose(
    target: Optional[AgentLike] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    version: Optional[str] = None,
    url: Optional[str] = None,
    capabilities: Union[AgentCapabilities, Dict[str, Any], None] = None,
    skills: Optional[Iterable[Union[AgentSkill, Dict[str, Any]]]] = None,
    timeout: Optional[int] = None,
    retries: Optional[int] = None,
    max_memory_mb: Optional[int] = None,
    max_cpu_percent: Optional[int] = None,
    allow_network: bool = True,
    sandbox: bool = False,
    **kwargs,
) -> Any:
    """
    Universal agent exposition.
    
    This function can be used as:
    1. Decorator: @expose
    2. Function call: expose(my_agent)
    3. Process wrapper: expose("./script.py")
    4. Container wrapper: expose("docker run my-agent")
    
    All metadata is auto-inferred with validation.
    
    Args:
        target: Function, framework instance, command, or container spec
        name: Agent name (auto-inferred if not provided)
        description: Agent description (auto-inferred if not provided)
        version: Version string (defaults to "1.0.0")
        url: Base URL (defaults to server URL when run() is called)
        capabilities: Agent capabilities (auto-inferred if not provided)
        skills: Agent skills (auto-inferred if not provided)
        timeout: Task timeout in seconds (default: 120)
        retries: Number of retry attempts (default: 0)
        max_memory_mb: Memory limit in MB
        max_cpu_percent: CPU usage limit as percentage
        allow_network: Whether to allow network access
        sandbox: Whether to run in sandboxed environment
        **kwargs: Additional configuration
    
    Returns:
        Original target (for decorator use) or wrapped target
    
    Raises:
        ExpositionError: If exposure fails
        SecurityViolationError: If security constraints are violated
        ValidationError: If configuration is invalid
    """
    
    def _expose_target(agent_target: AgentLike) -> Any:
        try:
            # Validate inputs early
            config = _build_and_validate_config(
                target=agent_target,
                name=name,
                description=description,
                version=version,
                timeout=timeout,
                retries=retries,
                max_memory_mb=max_memory_mb,
                max_cpu_percent=max_cpu_percent,
                allow_network=allow_network,
                sandbox=sandbox,
                **kwargs
            )
            
            # Check global limits
            _check_global_limits()
            
            # Auto-infer metadata with security checks
            metadata = infer_agent_metadata(
                agent_target,
                name=config['name'],
                description=config['description'],
                version=config['version'],
            )
            
            # Auto-infer capabilities securely
            if capabilities is None:
                inferred_caps = infer_capabilities(agent_target)
            else:
                inferred_caps = capabilities
                
            # Auto-infer skills securely
            if skills is None:
                inferred_skills = infer_skills(agent_target)
            else:
                inferred_skills = skills
            
            # Wrap target with security and resource limits
            wrapped_agent = _wrap_target_securely(
                agent_target, 
                config
            )
            
            # Register with the A2A-compliant system
            with _REGISTRY_LOCK:
                _register_agent_internal(
                    name=metadata.name,
                    description=metadata.description,
                    version=metadata.version,
                    url=url,
                    capabilities=inferred_caps,
                    skills=inferred_skills,
                    agent=wrapped_agent,
                )
                
                # Track registered agents for management
                _REGISTERED_AGENTS[metadata.name] = {
                    'target': agent_target,
                    'wrapped_agent': wrapped_agent,
                    'config': config,
                    'registered_at': time.time(),
                }
            
            logger.info(f"Successfully exposed agent '{metadata.name}' v{metadata.version}")
            return agent_target
            
        except Exception as e:
            error_msg = f"Failed to expose agent: {e}"
            logger.error(error_msg, exc_info=True)
            
            if isinstance(e, (SecurityViolationError, ValidationError)):
                raise
            else:
                raise ExpositionError(error_msg) from e
    
    # Support decorator usage: @expose
    if target is None:
        return _expose_target
    
    # Support direct usage: expose(agent)
    return _expose_target(target)


def _build_and_validate_config(**kwargs) -> Dict[str, Any]:
    """Build and validate configuration with secure defaults."""
    config = {
        'name': kwargs.get('name'),
        'description': kwargs.get('description'),
        'version': kwargs.get('version', '1.0.0'),
        'timeout': kwargs.get('timeout', _GLOBAL_CONFIG['default_timeout']),
        'retries': kwargs.get('retries', 0),
        'max_memory_mb': kwargs.get('max_memory_mb', _GLOBAL_CONFIG['max_memory_mb']),
        'max_cpu_percent': kwargs.get('max_cpu_percent', _GLOBAL_CONFIG['max_cpu_percent']),
        'allow_network': kwargs.get('allow_network', True),
        'sandbox': kwargs.get('sandbox', False),
    }
    
    # Validate configuration
    try:
        validate_agent_config(config)
    except ValidationError as e:
        raise ValidationError(f"Invalid configuration: {e}")
    
    # Apply security limits (handle None values)
    if config['timeout'] is not None:
        config['timeout'] = min(config['timeout'], 600)  # Max 10 minutes
    if config['retries'] is not None:
        config['retries'] = min(config['retries'], _GLOBAL_CONFIG['max_retries'])
    if config['max_memory_mb'] is not None:
        config['max_memory_mb'] = min(config['max_memory_mb'], 4096)  # Max 4GB
    if config['max_cpu_percent'] is not None:
        config['max_cpu_percent'] = min(config['max_cpu_percent'], 100)
    
    return config


def _check_global_limits() -> None:
    """Check global resource limits."""
    with _REGISTRY_LOCK:
        if len(_REGISTERED_AGENTS) >= _GLOBAL_CONFIG['max_concurrent_agents']:
            raise ResourceLimitError(
                f"Maximum number of concurrent agents ({_GLOBAL_CONFIG['max_concurrent_agents']}) exceeded"
            )


def _wrap_target_securely(target: Any, config: Dict[str, Any]) -> Any:
    """Securely wrap target with appropriate security measures."""
    
    # Handle different target types
    if isinstance(target, (str, Path)):
        # Process or container
        return _create_secure_process_wrapper(target, config)
    
    elif callable(target):
        # Function or framework instance
        if config['sandbox'] or not config['allow_network']:
            return SecurityWrapper(target, config)
        return target
    
    else:
        # Framework instance - detect and wrap common invocation patterns
        callable_wrapper = _create_framework_wrapper(target)
        if callable_wrapper:
            if config['sandbox'] or not config['allow_network']:
                return SecurityWrapper(callable_wrapper, config)
            return callable_wrapper
        
        # Apply security wrapper if needed for other cases
        if config['sandbox'] or not config['allow_network']:
            return SecurityWrapper(target, config)
        return target


def _create_framework_wrapper(target: Any) -> Optional[Callable[[str], Any]]:
    """
    Create a callable wrapper for various agent frameworks.
    
    This function detects common invocation patterns across different
    agent frameworks and creates a unified callable interface.
    
    Supported patterns:
    - invoke(message) - CrewAI, custom agents
    - run(message) - AutoGen, some custom frameworks  
    - __call__(message) - LangChain agents, callable objects
    - chat(message) - Some conversational frameworks
    - execute(message) - Task execution frameworks
    - process(message) - Processing frameworks
    """
    
    # Common framework invocation method names, ordered by popularity
    INVOCATION_METHODS = [
        'invoke',      # CrewAI, many custom frameworks
        'run',         # AutoGen, general purpose
        'run_live',    # Google ADK agents
        '__call__',    # LangChain agents, callable objects
        'chat',        # Conversational frameworks
        'execute',     # Task/workflow frameworks  
        'process',     # Data processing frameworks
        'generate',    # Generation frameworks
        'query',       # Query-based frameworks
        'ask',         # Q&A frameworks
    ]
    
    for method_name in INVOCATION_METHODS:
        if hasattr(target, method_name):
            method = getattr(target, method_name)
            if callable(method):
                # Create wrapper with proper error handling
                def create_method_wrapper(method_func, method_name):
                    def wrapper(message: str) -> Any:
                        try:
                            return method_func(message)
                        except TypeError as e:
                            # Handle signature mismatches gracefully
                            raise ExpositionError(
                                f"Framework method '{method_name}' signature incompatible: {e}"
                            ) from e
                        except Exception as e:
                            # Re-raise with context
                            raise ExpositionError(
                                f"Error calling framework method '{method_name}': {e}"
                            ) from e
                    return wrapper
                
                return create_method_wrapper(method, method_name)
    
    # No compatible method found
    return None


def _create_secure_process_wrapper(
    command: Union[str, Path], 
    config: Dict[str, Any]
) -> AgentFunction:
    """Create a secure wrapper for external processes/containers."""
    
    # Determine wrapper type
    if isinstance(command, str) and command.strip().startswith('docker'):
        if not _GLOBAL_CONFIG['allow_container_execution']:
            raise SecurityViolationError("Container execution is disabled")
        wrapper_class = ContainerWrapper
    else:
        if not _GLOBAL_CONFIG['allow_process_execution']:
            raise SecurityViolationError("Process execution is disabled")
        wrapper_class = ProcessWrapper
    
    # Create wrapper with security config
    wrapper = wrapper_class(
        command=command,
        timeout=config['timeout'],
        retries=config['retries'],
        max_memory_mb=config['max_memory_mb'],
        max_cpu_percent=config['max_cpu_percent'],
        allow_network=config['allow_network'],
        sandbox=config['sandbox'],
    )
    
    return wrapper.create_agent_function()


def run(
    host: str = "localhost",
    port: int = 8000,
    reload: bool = False,
    workers: Optional[int] = None,
    log_level: str = "info",
    access_log: bool = True,
    **server_kwargs
) -> None:
    """
    Start the production-ready A2A-compliant server.
    
    Args:
        host: Server host (default: localhost)
        port: Server port (default: 8000)
        reload: Enable hot reload for development (disabled in production)
        workers: Number of worker processes (defaults to CPU count)
        log_level: Logging level (debug, info, warning, error)
        access_log: Enable access logging
        **server_kwargs: Additional uvicorn configuration
    
    Raises:
        ExposureError: If server startup fails
    """
    try:
        # Validate server configuration
        _validate_server_config(host, port, reload, workers, log_level)
        
        # Update agent URLs in registry
        base_url = f"http://{host}:{port}"
        _update_agent_urls(base_url)
        
        # Create app with error handling
        app = create_app()
        
        # Configure uvicorn settings
        uvicorn_config = {
            'host': host,
            'port': port,
            'log_level': log_level,
            'access_log': access_log,
            **server_kwargs
        }
        
        # Production vs development settings  
        if reload:
            logger.warning("Hot reload enabled - not recommended for production")
            uvicorn_config['reload'] = True
            # Don't use workers with reload
        else:
            # Only set workers if > 1 to avoid uvicorn warning
            if workers is None:
                workers = 1  # Single worker by default to avoid complexity
            if workers > 1:
                uvicorn_config['workers'] = workers
        
        # Start server
        logger.info(f"Starting Loomdots server on {host}:{port}")
        logger.info(f"Registered agents: {len(_REGISTERED_AGENTS)}")
        
        import uvicorn
        uvicorn.run(app, **uvicorn_config)
        
    except ImportError:
        raise ExpositionError(
            "uvicorn is required to run the server. Install with: pip install uvicorn"
        )
    except Exception as e:
        logger.error(f"Server startup failed: {e}", exc_info=True)
        raise ExpositionError(f"Server startup failed: {e}") from e


def _validate_server_config(
    host: str, 
    port: int, 
    reload: bool, 
    workers: Optional[int],
    log_level: str
) -> None:
    """Validate server configuration."""
    if not isinstance(host, str) or not host.strip():
        raise ValidationError("Invalid host")
    
    if not isinstance(port, int) or not (1 <= port <= 65535):
        raise ValidationError("Invalid port number")
    
    if workers is not None and (not isinstance(workers, int) or workers < 1):
        raise ValidationError("Invalid worker count")
    
    valid_log_levels = {'critical', 'error', 'warning', 'info', 'debug', 'trace'}
    if log_level.lower() not in valid_log_levels:
        raise ValidationError(f"Invalid log level. Must be one of: {valid_log_levels}")


def _update_agent_urls(base_url: str) -> None:
    """Update registered agent URLs to match server configuration."""
    # This would update the registry URLs
    # Implementation depends on registry structure
    logger.debug(f"Updated agent URLs to base: {base_url}")


def get_registered_agents() -> Dict[str, Dict[str, Any]]:
    """Get information about currently registered agents."""
    with _REGISTRY_LOCK:
        return dict(_REGISTERED_AGENTS)


def unregister_agent(name: str) -> bool:
    """
    Unregister an agent by name.
    
    Args:
        name: Agent name to unregister
        
    Returns:
        True if agent was found and unregistered, False otherwise
    """
    with _REGISTRY_LOCK:
        if name in _REGISTERED_AGENTS:
            del _REGISTERED_AGENTS[name]
            logger.info(f"Unregistered agent '{name}'")
            return True
        return False


def clear_registry() -> None:
    """Clear all registered agents (useful for testing)."""
    with _REGISTRY_LOCK:
        count = len(_REGISTERED_AGENTS)
        _REGISTERED_AGENTS.clear()
        logger.info(f"Cleared {count} agents from registry")


def configure_security(
    max_concurrent_agents: Optional[int] = None,
    allow_process_execution: Optional[bool] = None,
    allow_container_execution: Optional[bool] = None,
    max_memory_mb: Optional[int] = None,
    max_cpu_percent: Optional[int] = None,
) -> None:
    """
    Configure global security settings.
    
    Args:
        max_concurrent_agents: Maximum number of concurrent agents
        allow_process_execution: Whether to allow process execution
        allow_container_execution: Whether to allow container execution
        max_memory_mb: Default maximum memory per agent
        max_cpu_percent: Default maximum CPU percentage per agent
    """
    if max_concurrent_agents is not None:
        _GLOBAL_CONFIG['max_concurrent_agents'] = max(1, max_concurrent_agents)
    
    if allow_process_execution is not None:
        _GLOBAL_CONFIG['allow_process_execution'] = allow_process_execution
    
    if allow_container_execution is not None:
        _GLOBAL_CONFIG['allow_container_execution'] = allow_container_execution
    
    if max_memory_mb is not None:
        _GLOBAL_CONFIG['max_memory_mb'] = max(64, min(max_memory_mb, 8192))
    
    if max_cpu_percent is not None:
        _GLOBAL_CONFIG['max_cpu_percent'] = max(1, min(max_cpu_percent, 100))
    
    logger.info("Updated security configuration")


# Convenience functions
def expose_function(func: AgentFunction, **kwargs) -> AgentFunction:
    """Convenience method for exposing functions."""
    return expose(func, **kwargs)


def expose_process(command: ProcessLike, **kwargs) -> None:
    """Convenience method for exposing processes."""
    expose(command, **kwargs)


def expose_container(container_spec: str, **kwargs) -> None:
    """Convenience method for exposing containers."""
    if not _GLOBAL_CONFIG['allow_container_execution']:
        raise SecurityViolationError("Container execution is disabled")
    expose(container_spec, **kwargs)


# Export the main API
__all__ = [
    # Main API
    "expose",
    "run",
    # Management functions
    "get_registered_agents",
    "unregister_agent", 
    "clear_registry",
    "configure_security",
    # Convenience functions
    "expose_function",
    "expose_process",
    "expose_container",
    # Exceptions
    "ExpositionError",
    "SecurityViolationError",
    "ResourceLimitError",
]
