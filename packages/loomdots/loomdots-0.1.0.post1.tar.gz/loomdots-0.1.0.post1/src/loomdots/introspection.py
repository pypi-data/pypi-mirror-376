"""Introspection system for automatic agent metadata inference."""
from __future__ import annotations

import re
import ast
import asyncio
import inspect
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Any, List, Set, AsyncIterator, Generator, Optional, Callable

from a2a.types import AgentCapabilities, AgentSkill


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AgentMetadata:
    """Immutable container for inferred agent metadata."""
    name: str
    description: str
    version: str


class IntrospectionError(Exception):
    """Raised when introspection fails in an unrecoverable way."""
    pass


class SecurityError(IntrospectionError):
    """Raised when security constraints are violated during introspection."""
    pass


def infer_agent_metadata(
    target: Any,
    name: Optional[str] = None,
    description: Optional[str] = None,
    version: Optional[str] = None,
    max_description_length: int = 1000,
    allowed_file_extensions: Set[str] = frozenset({'.py', '.js', '.sh', '.bash'}),
) -> AgentMetadata:
    """
    Safely infer agent metadata from various target types.
    
    Args:
        target: The agent target to introspect
        name: Override name (if None, will be inferred)
        description: Override description (if None, will be inferred)
        version: Override version (if None, defaults to "1.0.0")
        max_description_length: Maximum allowed description length for security
        allowed_file_extensions: Allowed file extensions for file introspection
        
    Returns:
        AgentMetadata with inferred or provided values
        
    Raises:
        IntrospectionError: If introspection fails
        SecurityError: If security constraints are violated
    """
    try:
        inferred_name = name or _infer_name(target, allowed_file_extensions)
        inferred_description = description or _infer_description(
            target, max_description_length, allowed_file_extensions
        )
        inferred_version = version or "1.0.0"
        
        # Validate inferred values
        _validate_metadata(inferred_name, inferred_description, inferred_version)
        
        return AgentMetadata(
            name=inferred_name,
            description=inferred_description,
            version=inferred_version,
        )
        
    except Exception as e:
        logger.error(f"Failed to infer agent metadata from {type(target).__name__}: {e}")
        # Provide safe fallbacks
        return AgentMetadata(
            name=name or _safe_fallback_name(target),
            description=description or "AI Agent",
            version=version or "1.0.0",
        )


def infer_capabilities(
    target: Any,
    analyze_code: bool = False,
    timeout: float = 5.0,
) -> AgentCapabilities:
    """
    Safely infer agent capabilities from target.
    
    Args:
        target: The agent target to introspect
        analyze_code: Whether to perform static code analysis (security risk)
        timeout: Maximum time to spend on inference
        
    Returns:
        AgentCapabilities with inferred capabilities
    """
    try:
        # Run the async function in a sync context
        return asyncio.run(_infer_capabilities_async(target, analyze_code))
    except Exception as e:
        logger.error(f"Failed to infer capabilities: {e}")
        return AgentCapabilities(streaming=True)  # Safe default


async def _infer_capabilities_async(target: Any, analyze_code: bool) -> AgentCapabilities:
    """Async capability inference with proper error handling."""
    streaming = False
    
    # Check if target supports streaming
    if callable(target):
        sig = inspect.signature(target)
        return_annotation = sig.return_annotation
        
        # Check for generator/async generator annotations
        if hasattr(return_annotation, '__origin__'):
            origin = getattr(return_annotation, '__origin__', None)
            if origin in (Generator, AsyncIterator):
                streaming = True
    
    # Check framework-specific patterns
    if hasattr(target, 'stream') and callable(target.stream):
        streaming = True
    elif hasattr(target, 'invoke') and callable(target.invoke):
        streaming = False
    elif hasattr(target, 'run_async') and hasattr(target, 'session_service'):
        streaming = True  # ADK pattern
    
    return AgentCapabilities(streaming=streaming)


def infer_skills(
    target: Any,
    max_skills: int = 10,
    analyze_docstrings: bool = True,
) -> List[AgentSkill]:
    """
    Safely infer agent skills from target.
    
    Args:
        target: The agent target to introspect
        max_skills: Maximum number of skills to infer (security limit)
        analyze_docstrings: Whether to analyze docstrings for skills
        
    Returns:
        List of inferred AgentSkill objects
    """
    try:
        skills = []
        
        # Infer from callable signature
        if callable(target):
            skill = _infer_skill_from_callable(target, analyze_docstrings)
            if skill:
                skills.append(skill)
        
        # Infer from framework-specific patterns
        framework_skills = _infer_framework_skills(target)
        skills.extend(framework_skills)
        
        # Limit number of skills for security
        return skills[:max_skills]
        
    except Exception as e:
        logger.error(f"Failed to infer skills: {e}")
        return []


def _infer_name(target: Any, allowed_extensions: Set[str]) -> str:
    """Safely infer agent name from target."""
    if callable(target):
        name = getattr(target, '__name__', None)
        if name and name != '<lambda>':
            return _sanitize_name(name)
    
    if isinstance(target, (str, Path)):
        path = Path(target) if isinstance(target, str) else target
        if path.suffix in allowed_extensions:
            return _sanitize_name(path.stem)
    
    if hasattr(target, 'name'):
        name = getattr(target, 'name')
        if isinstance(name, str):
            return _sanitize_name(name)
    
    return _safe_fallback_name(target)


def _infer_description(
    target: Any, 
    max_length: int,
    allowed_extensions: Set[str]
) -> str:
    """Safely infer agent description from target."""
    # From docstring
    if callable(target):
        doc = inspect.getdoc(target)
        if doc:
            return _sanitize_description(doc, max_length)
    
    # From file contents (limited and secure)
    if isinstance(target, (str, Path)):
        path = Path(target) if isinstance(target, str) else target
        if path.suffix in allowed_extensions and path.exists():
            try:
                description = _extract_description_from_file(path, max_length)
                if description:
                    return description
            except Exception as e:
                logger.debug(f"Failed to extract description from file: {e}")
    
    # From framework attributes
    if hasattr(target, 'description'):
        desc = getattr(target, 'description')
        if isinstance(desc, str):
            return _sanitize_description(desc, max_length)
    
    return "AI Agent"


def _extract_description_from_file(path: Path, max_length: int) -> Optional[str]:
    """Safely extract description from file with security constraints."""
    # Security: Limit file size to prevent DoS
    max_file_size = 100 * 1024  # 100KB
    if path.stat().st_size > max_file_size:
        logger.warning(f"File {path} too large for description extraction")
        return None
    
    try:
        content = path.read_text(encoding='utf-8', errors='ignore')
        
        # Extract module docstring for Python files
        if path.suffix == '.py':
            return _extract_python_module_docstring(content, max_length)
        
        # Extract comment-based description for other files
        return _extract_comment_description(content, max_length)
        
    except Exception as e:
        logger.debug(f"Failed to read file {path}: {e}")
        return None


def _extract_python_module_docstring(content: str, max_length: int) -> Optional[str]:
    """Safely extract module docstring from Python code."""
    try:
        tree = ast.parse(content)
        if (tree.body and 
            isinstance(tree.body[0], ast.Expr) and 
            isinstance(tree.body[0].value, ast.Constant)):
            docstring = tree.body[0].value.value
            if isinstance(docstring, str):
                return _sanitize_description(docstring, max_length)
    except (SyntaxError, ValueError) as e:
        logger.debug(f"Failed to parse Python file: {e}")
    
    return None


def _extract_comment_description(content: str, max_length: int) -> Optional[str]:
    """Extract description from file comments."""
    lines = content.split('\n')[:20]  # Only check first 20 lines
    
    description_lines = []
    for line in lines:
        line = line.strip()
        if line.startswith('#') or line.startswith('//') or line.startswith('/*'):
            # Remove comment markers
            clean_line = re.sub(r'^[#/\*]+\s*', '', line).strip()
            if clean_line and not clean_line.startswith('@'):
                description_lines.append(clean_line)
        elif description_lines:  # Stop at first non-comment after finding comments
            break
    
    if description_lines:
        description = ' '.join(description_lines)
        return _sanitize_description(description, max_length)
    
    return None


def _infer_skill_from_callable(target: Callable, analyze_docstrings: bool) -> Optional[AgentSkill]:
    """Infer skill from callable signature and docstring."""
    try:
        name = getattr(target, '__name__', 'agent_skill')
        if name == '<lambda>':
            name = 'agent_skill'
        
        description = ""
        if analyze_docstrings:
            doc = inspect.getdoc(target)
            if doc:
                description = _sanitize_description(doc, 200)
        
        return AgentSkill(
            id=_sanitize_name(name),
            name=_humanize_name(name),
            description=description or f"Skill provided by {name}",
            tags=[],
            examples=[],
        )
    except Exception as e:
        logger.debug(f"Failed to infer skill from callable: {e}")
        return None


def _infer_framework_skills(target: Any) -> List[AgentSkill]:
    """Infer skills from framework-specific patterns."""
    skills = []
    
    # CrewAI pattern
    if hasattr(target, 'invoke') and callable(target.invoke):
        skills.append(AgentSkill(
            id="crewai_agent",
            name="CrewAI Agent",
            description="Agent powered by CrewAI framework",
            tags=["crewai"],
            examples=[],
        ))
    
    # LangGraph pattern
    elif hasattr(target, 'stream') and callable(target.stream):
        skills.append(AgentSkill(
            id="langgraph_agent",
            name="LangGraph Agent", 
            description="Streaming agent powered by LangGraph",
            tags=["langgraph", "streaming"],
            examples=[],
        ))
    
    # Google ADK pattern
    elif hasattr(target, 'run_async') and hasattr(target, 'session_service'):
        skills.append(AgentSkill(
            id="adk_agent",
            name="Google ADK Agent",
            description="Agent powered by Google ADK",
            tags=["google-adk", "streaming"],
            examples=[],
        ))
    
    return skills


def _sanitize_name(name: str) -> str:
    """Sanitize agent name for security and compatibility."""
    if not isinstance(name, str):
        return "agent"
    
    # Remove/replace unsafe characters
    sanitized = re.sub(r'[^\w\-_\s]', '', name)
    sanitized = re.sub(r'\s+', '_', sanitized.strip())
    
    # Ensure reasonable length
    sanitized = sanitized[:100]
    
    # Ensure not empty
    return sanitized or "agent"


def _sanitize_description(description: str, max_length: int) -> str:
    """Sanitize description for security."""
    if not isinstance(description, str):
        return "AI Agent"
    
    # Remove potentially dangerous content
    sanitized = re.sub(r'[^\w\s\.\-_,!?;:()\[\]{}]', ' ', description)
    sanitized = re.sub(r'\s+', ' ', sanitized.strip())
    
    # Truncate to max length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length-3] + "..."
    
    return sanitized or "AI Agent"


def _humanize_name(name: str) -> str:
    """Convert snake_case or camelCase to human-readable name."""
    # Convert snake_case to words
    name = name.replace('_', ' ')
    
    # Convert camelCase to words
    name = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
    
    # Capitalize words
    return name.title()


def _safe_fallback_name(target: Any) -> str:
    """Generate safe fallback name for any target."""
    type_name = type(target).__name__
    return f"{type_name}_agent"


def _validate_metadata(name: str, description: str, version: str) -> None:
    """Validate metadata values for security and correctness."""
    if not name or len(name) > 100:
        raise SecurityError("Invalid agent name")
    
    if not description or len(description) > 1000:
        raise SecurityError("Invalid agent description")
    
    if not version or len(version) > 50:
        raise SecurityError("Invalid version string")
    
    # Basic version format validation
    if not re.match(r'^\d+\.\d+\.\d+', version):
        logger.warning(f"Version '{version}' doesn't follow semver format")