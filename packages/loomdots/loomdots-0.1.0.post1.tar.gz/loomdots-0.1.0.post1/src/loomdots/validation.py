"""Comprehensive validation module for agent configuration and security."""

from __future__ import annotations

import re
import psutil
from pathlib import Path
from typing import Any, Dict, Optional, Union


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


class SecurityValidationError(ValidationError):
    """Raised when security validation fails."""
    pass


# Security constraints
MAX_NAME_LENGTH = 100
MAX_DESCRIPTION_LENGTH = 1000
MAX_VERSION_LENGTH = 50
MIN_TIMEOUT = 1
MAX_TIMEOUT = 3600  # 60 minutes
MAX_RETRIES = 10
MAX_MEMORY_MB = 8192  # 8GB
MAX_CPU_PERCENT = 100
MIN_PORT = 1024  # Avoid privileged ports
MAX_PORT = 65535

# Allowed patterns
NAME_PATTERN = re.compile(r'^[a-zA-Z][a-zA-Z0-9_\-\s]{0,99}$')
VERSION_PATTERN = re.compile(r'^\d+\.\d+\.\d+([a-zA-Z0-9\-\+\.]*)?$')
HOST_PATTERN = re.compile(r'^[a-zA-Z0-9\-\.]+(:\d+)?$')

# Dangerous patterns to block
DANGEROUS_COMMAND_PATTERNS = [
    r'rm\s+\-rf',
    r'sudo',
    r'su\s+',
    r'passwd',
    r'chmod\s+777',
    r'curl.*\|.*sh',
    r'wget.*\|.*sh',
    r'eval',
    r'exec',
    r'system\(',
    r'subprocess\.call',
    r'os\.system',
    r'\$\(',  # Command substitution
    r'`',     # Backticks
    r'&&',    # Command chaining
    r'\|\|',  # Command chaining
    r';',     # Command separator
]

DANGEROUS_FILE_EXTENSIONS = {
    '.exe', '.bat', '.cmd', '.com', '.scr', '.pif', '.vbs', '.vbe',
    '.js', '.jar', '.msi', '.dll', '.so', '.dylib'
}

ALLOWED_FILE_EXTENSIONS = {
    '.py', '.js', '.sh', '.bash', '.zsh', '.fish', '.pl', '.rb',
    '.go', '.rs', '.java', '.kt', '.scala', '.clj'
}


def validate_agent_config(config: Dict[str, Any]) -> None:
    """
    Validate complete agent configuration.
    
    Args:
        config: Configuration dictionary to validate
        
    Raises:
        ValidationError: If configuration is invalid
        SecurityValidationError: If configuration violates security constraints
    """
    validate_agent_name(config.get('name'))
    validate_agent_description(config.get('description'))
    validate_version(config.get('version'))
    validate_timeout(config.get('timeout'))
    validate_retries(config.get('retries'))
    validate_memory_limit(config.get('max_memory_mb'))
    validate_cpu_limit(config.get('max_cpu_percent'))


def validate_agent_name(name: Optional[str]) -> None:
    """Validate agent name for security and compatibility."""
    if name is None:
        return  # Will be auto-generated
        
    if not isinstance(name, str):
        raise ValidationError("Agent name must be a string")
    
    if len(name) > MAX_NAME_LENGTH:
        raise ValidationError(f"Agent name too long (max {MAX_NAME_LENGTH} characters)")
    
    if not NAME_PATTERN.match(name):
        raise ValidationError(
            "Agent name must start with letter and contain only letters, "
            "numbers, underscores, hyphens, and spaces"
        )
    
    # Check for reserved names
    reserved_names = {'admin', 'root', 'system', 'api', 'health', 'status'}
    if name.lower() in reserved_names:
        raise SecurityValidationError(f"Agent name '{name}' is reserved")


def validate_agent_description(description: Optional[str]) -> None:
    """Validate agent description for security."""
    if description is None:
        return  # Will be auto-generated
        
    if not isinstance(description, str):
        raise ValidationError("Agent description must be a string")
    
    if len(description) > MAX_DESCRIPTION_LENGTH:
        raise ValidationError(f"Description too long (max {MAX_DESCRIPTION_LENGTH} characters)")
    
    # Check for potentially dangerous content
    dangerous_patterns = [
        r'<script',
        r'javascript:',
        r'data:text/html',
        r'eval\(',
        r'document\.write',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, description, re.IGNORECASE):
            raise SecurityValidationError(f"Description contains dangerous patterns: {pattern}")


def validate_version(version: Optional[str]) -> None:
    """Validate version string."""
    if version is None:
        return
        
    if not isinstance(version, str):
        raise ValidationError("Version must be a string")
    
    if len(version) > MAX_VERSION_LENGTH:
        raise ValidationError(f"Version string too long (max {MAX_VERSION_LENGTH} characters)")
    
    if not VERSION_PATTERN.match(version):
        raise ValidationError("Version must follow semantic versioning (e.g., 1.0.0)")


def validate_timeout(timeout: Optional[int]) -> None:
    """Validate timeout value."""
    if timeout is None:
        return
        
    if not isinstance(timeout, int):
        raise ValidationError("Timeout must be an integer")
    
    if timeout < MIN_TIMEOUT:
        raise ValidationError(f"Timeout too small (minimum {MIN_TIMEOUT} seconds)")
    
    if timeout > MAX_TIMEOUT:
        raise ValidationError(f"Timeout too large (maximum {MAX_TIMEOUT} seconds)")


def validate_retries(retries: Optional[int]) -> None:
    """Validate retry count."""
    if retries is None:
        return
        
    if not isinstance(retries, int):
        raise ValidationError("Retries must be an integer")
    
    if retries < 0:
        raise ValidationError("Retries cannot be negative")
    
    if retries > MAX_RETRIES:
        raise ValidationError(f"Too many retries (maximum {MAX_RETRIES})")


def validate_memory_limit(memory_mb: Optional[int]) -> None:
    """Validate memory limit."""
    if memory_mb is None:
        return
        
    if not isinstance(memory_mb, int):
        raise ValidationError("Memory limit must be an integer")
    
    if memory_mb < 64:
        raise ValidationError("Memory limit too small (minimum 64 MB)")
    
    if memory_mb > MAX_MEMORY_MB:
        raise ValidationError(f"Memory limit too large (maximum {MAX_MEMORY_MB} MB)")
    
    # Check against system memory
    try:
        system_memory_mb = psutil.virtual_memory().total // (1024 * 1024)
        if memory_mb > system_memory_mb * 0.8:  # Don't use more than 80% of system memory
            raise SecurityValidationError(
                f"Memory limit ({memory_mb} MB) exceeds safe system limit "
                f"({int(system_memory_mb * 0.8)} MB)"
            )
    except Exception:
        # If psutil fails, just continue with basic validation
        pass


def validate_cpu_limit(cpu_percent: Optional[int]) -> None:
    """Validate CPU limit."""
    if cpu_percent is None:
        return
        
    if not isinstance(cpu_percent, int):
        raise ValidationError("CPU limit must be an integer")
    
    if cpu_percent < 1:
        raise ValidationError("CPU limit too small (minimum 1%)")
    
    if cpu_percent > MAX_CPU_PERCENT:
        raise ValidationError(f"CPU limit too large (maximum {MAX_CPU_PERCENT}%)")


def validate_command(command: Union[str, Path]) -> None:
    """
    Validate command for security vulnerabilities.
    
    Args:
        command: Command string or path to validate
        
    Raises:
        SecurityValidationError: If command is potentially dangerous
    """
    command_str = str(command)
    
    # Check for dangerous patterns
    for pattern in DANGEROUS_COMMAND_PATTERNS:
        if re.search(pattern, command_str, re.IGNORECASE):
            raise SecurityValidationError(f"Command contains dangerous pattern: {pattern}")
    
    # If it's a file path, validate the file
    if isinstance(command, Path) or (isinstance(command, str) and not command.startswith('docker')):
        validate_executable_file(command)


def validate_executable_file(file_path: Union[str, Path]) -> None:
    """
    Validate executable file for security.
    
    Args:
        file_path: Path to executable file
        
    Raises:
        ValidationError: If file is invalid
        SecurityValidationError: If file violates security constraints
    """
    path = Path(file_path)
    
    # Check if file exists
    if not path.exists():
        raise ValidationError(f"File does not exist: {path}")
    
    # Check file extension
    if path.suffix.lower() in DANGEROUS_FILE_EXTENSIONS:
        raise SecurityValidationError(f"Dangerous file extension: {path.suffix}")
    
    if path.suffix.lower() not in ALLOWED_FILE_EXTENSIONS:
        # Allow files without extension if they're executable
        if not (path.suffix == '' and path.is_file() and path.stat().st_mode & 0o111):
            raise ValidationError(f"Unsupported file type: {path.suffix}")
    
    # Check file size (prevent huge files)
    try:
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > 100:  # 100MB limit
            raise SecurityValidationError(f"File too large: {size_mb:.1f} MB (max 100 MB)")
    except Exception as e:
        raise ValidationError(f"Cannot access file: {e}")
    
    # Basic content validation for script files
    if path.suffix.lower() in {'.py', '.js', '.sh', '.bash'}:
        validate_script_content(path)


def validate_script_content(script_path: Path) -> None:
    """
    Validate script content for basic security issues.
    
    Args:
        script_path: Path to script file
        
    Raises:
        SecurityValidationError: If script contains dangerous patterns
    """
    try:
        # Only read first 10KB to avoid DoS
        content = script_path.read_text(encoding='utf-8', errors='ignore')[:10240]
        
        # Check for dangerous patterns
        for pattern in DANGEROUS_COMMAND_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                raise SecurityValidationError(
                    f"Script contains dangerous pattern: {pattern}"
                )
        
        # Check for suspicious network activity patterns
        suspicious_patterns = [
            r'curl\s+.*[^a-zA-Z0-9\-\.]',  # Suspicious curl usage
            r'wget\s+.*[^a-zA-Z0-9\-\.]',  # Suspicious wget usage
            r'nc\s+.*\d+',                 # Netcat usage
            r'telnet\s+',                  # Telnet usage
            r'/dev/tcp/',                  # TCP device access
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                raise SecurityValidationError(
                    f"Script contains suspicious network pattern: {pattern}"
                )
                
    except UnicodeDecodeError:
        # Binary file or encoding issue
        raise SecurityValidationError("Cannot validate binary or encoded script file")
    except Exception as e:
        raise ValidationError(f"Cannot read script file: {e}")


def validate_container_spec(container_spec: str) -> None:
    """
    Validate container specification for security.
    
    Args:
        container_spec: Docker container specification
        
    Raises:
        SecurityValidationError: If container spec is dangerous
    """
    if not isinstance(container_spec, str):
        raise ValidationError("Container spec must be a string")
    
    spec_lower = container_spec.lower()
    
    # Check for dangerous Docker flags
    dangerous_flags = [
        '--privileged',
        '--user root',
        '--user 0',
        '--net host',
        '--network host',
        '--pid host',
        '--ipc host',
        '--cap-add',
        '--security-opt',
        '--volume /:/host',
        '--mount.*type=bind.*source=/',
        '-v /:/host',
    ]
    
    for flag in dangerous_flags:
        if re.search(flag.replace(' ', r'\s+'), spec_lower):
            raise SecurityValidationError(f"Dangerous Docker flag detected: {flag}")
    
    # Ensure image name is reasonable
    if 'docker run' in spec_lower:
        # Extract image name
        parts = container_spec.split()
        try:
            run_index = parts.index('docker') + 1
            if run_index < len(parts) and parts[run_index] == 'run':
                # Find image name (skip flags)
                for i, part in enumerate(parts[run_index + 1:], run_index + 1):
                    if not part.startswith('-') and ':' not in part:
                        continue
                    # This is likely the image name
                    validate_image_name(part)
                    break
        except (ValueError, IndexError):
            raise ValidationError("Invalid Docker command format")


def validate_image_name(image_name: str) -> None:
    """Validate Docker image name for security."""
    if not re.match(r'^[a-zA-Z0-9\.\-_/:]+$', image_name):
        raise SecurityValidationError("Invalid characters in image name")
    
    # Block certain suspicious image patterns
    suspicious_patterns = [
        r'.*:latest$',  # Discourage latest tag
        r'^[^/]+$',     # Images without registry (could be local builds)
    ]
    
    for pattern in suspicious_patterns:
        if re.match(pattern, image_name):
            raise SecurityValidationError(f"Suspicious image pattern: {image_name}")


def validate_server_config(
    host: str,
    port: int,
    workers: Optional[int] = None,
    max_request_size: int = 10 * 1024 * 1024,  # 10MB
) -> None:
    """
    Validate server configuration.
    
    Args:
        host: Server host
        port: Server port
        workers: Number of workers
        max_request_size: Maximum request size in bytes
        
    Raises:
        ValidationError: If configuration is invalid
        SecurityValidationError: If configuration is insecure
    """
    # Validate host
    if not isinstance(host, str) or not host.strip():
        raise ValidationError("Host must be a non-empty string")
    
    if host != 'localhost' and host != '127.0.0.1' and not HOST_PATTERN.match(host):
        raise ValidationError("Invalid host format")
    
    # Security warning for public hosts
    if host in ('0.0.0.0', '::'):
        raise SecurityValidationError(
            "Binding to all interfaces (0.0.0.0 or ::) is a security risk. "
            "Use specific IP addresses or localhost for development."
        )
    
    # Validate port
    if not isinstance(port, int):
        raise ValidationError("Port must be an integer")
    
    if port < MIN_PORT:
        raise SecurityValidationError(
            f"Port {port} is privileged. Use ports >= {MIN_PORT} for security."
        )
    
    if port > MAX_PORT:
        raise ValidationError(f"Port {port} exceeds maximum ({MAX_PORT})")
    
    # Validate workers
    if workers is not None:
        if not isinstance(workers, int) or workers < 1:
            raise ValidationError("Workers must be a positive integer")
        
        cpu_count = psutil.cpu_count() or 1
        if workers > cpu_count * 2:
            raise ValidationError(
                f"Too many workers ({workers}) for system with {cpu_count} CPUs"
            )
    
    # Validate request size
    if max_request_size > 100 * 1024 * 1024:  # 100MB
        raise SecurityValidationError("Maximum request size is too large (max 100MB)")


def check_system_resources() -> Dict[str, Any]:
    """
    Check current system resource usage.
    
    Returns:
        Dictionary with system resource information
    """
    try:
        memory = psutil.virtual_memory()
        cpu_count = psutil.cpu_count()
        disk = psutil.disk_usage('/')
        
        return {
            'memory_total_gb': memory.total / (1024**3),
            'memory_available_gb': memory.available / (1024**3),
            'memory_percent': memory.percent,
            'cpu_count': cpu_count,
            'cpu_percent': psutil.cpu_percent(interval=1),
            'disk_free_gb': disk.free / (1024**3),
            'disk_percent': disk.percent,
        }
    except Exception as e:
        return {'error': str(e)}


def validate_resource_availability(
    required_memory_mb: int,
    required_cpu_percent: int
) -> None:
    """
    Validate that required resources are available.
    
    Args:
        required_memory_mb: Required memory in MB
        required_cpu_percent: Required CPU percentage
        
    Raises:
        ResourceUnavailableError: If resources are not available
    """
    try:
        # Check memory
        memory = psutil.virtual_memory()
        available_mb = memory.available / (1024 * 1024)
        
        if required_memory_mb > available_mb * 0.9:  # Leave 10% buffer
            raise ValidationError(
                f"Insufficient memory: need {required_memory_mb} MB, "
                f"available {int(available_mb)} MB"
            )
        
        # Check CPU (basic check)
        current_cpu = psutil.cpu_percent(interval=1)
        if current_cpu > 90:  # System under high load
            raise ValidationError(
                f"System under high CPU load ({current_cpu}%), "
                f"cannot guarantee {required_cpu_percent}% CPU"
            )
            
    except psutil.Error as e:
        # If psutil fails, just log and continue
        import logging
        logging.getLogger(__name__).warning(f"Could not check system resources: {e}")
        