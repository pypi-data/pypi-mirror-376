"""Secure wrappers for processes, containers, and functions with sandboxing and resource limits."""

from __future__ import annotations

import os
import sys
import time
import shlex
import psutil
import asyncio
import logging
import tempfile
import resource
import threading
import subprocess
from pathlib import Path
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, AsyncIterator, Callable, Dict, Generator, List, Optional, Union

from .validation import validate_command, validate_container_spec


logger = logging.getLogger(__name__)


# Type aliases
AgentFunction = Callable[[str], Union[str, Generator[str, None, None], AsyncIterator[str]]]


class WrapperError(Exception):
    """Base exception for wrapper errors."""
    pass


class SecurityWrapperError(WrapperError):
    """Raised when security wrapper encounters an error."""
    pass


class ResourceLimitExceededError(WrapperError):
    """Raised when resource limits are exceeded."""
    pass


class BaseWrapper(ABC):
    """Base class for all agent wrappers."""
    
    def __init__(
        self,
        timeout: int = 120,
        retries: int = 0,
        max_memory_mb: int = 1024,
        max_cpu_percent: int = 50,
        allow_network: bool = True,
        sandbox: bool = False,
    ):
        self.timeout = timeout
        self.retries = retries
        self.max_memory_mb = max_memory_mb
        self.max_cpu_percent = max_cpu_percent
        self.allow_network = allow_network
        self.sandbox = sandbox
        self._active_processes: Dict[int, psutil.Process] = {}
        self._process_lock = threading.Lock()
    
    @abstractmethod
    def create_agent_function(self) -> AgentFunction:
        """Create the agent function that will be called by the A2A framework."""
        pass
    
    def _register_process(self, process: psutil.Process) -> None:
        """Register a process for monitoring."""
        with self._process_lock:
            self._active_processes[process.pid] = process
    
    def _unregister_process(self, pid: int) -> None:
        """Unregister a process."""
        with self._process_lock:
            self._active_processes.pop(pid, None)
    
    def _cleanup_processes(self) -> None:
        """Clean up all active processes."""
        with self._process_lock:
            for pid, process in list(self._active_processes.items()):
                try:
                    if process.is_running():
                        process.terminate()
                        try:
                            process.wait(timeout=5)
                        except psutil.TimeoutExpired:
                            process.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                finally:
                    self._active_processes.pop(pid, None)
    
    def __del__(self):
        """Cleanup on destruction."""
        try:
            self._cleanup_processes()
        except Exception:
            pass


class ProcessWrapper(BaseWrapper):
    """Secure wrapper for external processes."""
    
    def __init__(self, command: Union[str, Path], **kwargs):
        super().__init__(**kwargs)
        self.command = command
        
        # Validate command for security
        validate_command(command)
        
        # Prepare command
        self._prepared_command = self._prepare_command()
    
    def _prepare_command(self) -> List[str]:
        """Prepare command for secure execution."""
        if isinstance(self.command, Path):
            # File path - determine how to execute
            if self.command.suffix == '.py':
                return [sys.executable, str(self.command)]
            elif self.command.suffix == '.js':
                return ['node', str(self.command)]
            elif self.command.suffix in {'.sh', '.bash'}:
                return ['bash', str(self.command)]
            elif self.command.is_file() and os.access(self.command, os.X_OK):
                return [str(self.command)]
            else:
                raise WrapperError(f"Don't know how to execute {self.command}")
        else:
            # String command - parse safely
            try:
                return shlex.split(self.command)
            except ValueError as e:
                raise WrapperError(f"Invalid command syntax: {e}")
    
    def create_agent_function(self) -> AgentFunction:
        """Create the agent function."""
        def process_agent(message: str) -> str:
            return self._execute_with_retries(message)
        
        return process_agent
    
    def _execute_with_retries(self, message: str) -> str:
        """Execute command with retry logic."""
        last_error = None
        
        for attempt in range(self.retries + 1):
            try:
                return self._execute_secure(message)
            except Exception as e:
                last_error = e
                if attempt < self.retries:
                    logger.warning(f"Attempt {attempt + 1} failed, retrying: {e}")
                    time.sleep(min(2 ** attempt, 10))  # Exponential backoff
                else:
                    logger.error(f"All {self.retries + 1} attempts failed")
        
        raise WrapperError(f"Command execution failed after {self.retries + 1} attempts: {last_error}")
    
    def _execute_secure(self, message: str) -> str:
        """Execute command with security constraints."""
        # Create secure environment
        env = self._create_secure_environment()
        
        # Set up resource limits
        preexec_fn = self._create_preexec_function()
        
        try:
            with self._create_temp_directory() as temp_dir:
                # Execute with timeout and resource limits
                process = subprocess.Popen(
                    self._prepared_command,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env,
                    cwd=temp_dir if self.sandbox else None,
                    preexec_fn=preexec_fn,
                )
                
                # Monitor the process
                psutil_process = psutil.Process(process.pid)
                self._register_process(psutil_process)
                
                try:
                    # Monitor resource usage
                    monitor_thread = threading.Thread(
                        target=self._monitor_resources,
                        args=(psutil_process,),
                        daemon=True
                    )
                    monitor_thread.start()
                    
                    # Execute with timeout
                    stdout, stderr = process.communicate(
                        input=message, 
                        timeout=self.timeout
                    )
                    
                    if process.returncode != 0:
                        raise WrapperError(f"Process failed with exit code {process.returncode}: {stderr}")
                    
                    return stdout.strip()
                
                finally:
                    self._unregister_process(process.pid)
                    
                    # Ensure process is terminated
                    if process.poll() is None:
                        try:
                            process.terminate()
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            process.kill()
        
        except subprocess.TimeoutExpired:
            raise ResourceLimitExceededError(f"Process timed out after {self.timeout} seconds")
        except Exception as e:
            if isinstance(e, WrapperError):
                raise
            raise WrapperError(f"Process execution failed: {e}")
    
    def _create_secure_environment(self) -> Dict[str, str]:
        """Create secure environment for process execution."""
        # Start with minimal environment
        env = {
            'PATH': '/usr/local/bin:/usr/bin:/bin',
            'HOME': '/tmp',
            'USER': 'nobody',
            'SHELL': '/bin/sh',
        }
        
        # Add Python path if executing Python
        if self._prepared_command[0] == sys.executable:
            env['PYTHONPATH'] = os.pathsep.join(sys.path)
            env['PYTHONUNBUFFERED'] = '1'
        
        # Disable network if requested
        if not self.allow_network:
            env['http_proxy'] = 'http://127.0.0.1:1'  # Invalid proxy
            env['https_proxy'] = 'http://127.0.0.1:1'
            env['HTTP_PROXY'] = 'http://127.0.0.1:1'
            env['HTTPS_PROXY'] = 'http://127.0.0.1:1'
        
        return env
    
    def _create_preexec_function(self) -> Optional[Callable[[], None]]:
        """Create preexec function for resource limits."""
        if os.name != 'posix':
            return None  # Resource limits not supported on Windows
        
        def preexec():
            # Set memory limit
            memory_bytes = self.max_memory_mb * 1024 * 1024
            try:
                resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
            except ValueError:
                # Limit might be too low, try with system limit
                pass
            
            # Set CPU time limit (soft limit)
            try:
                resource.setrlimit(resource.RLIMIT_CPU, (self.timeout * 2, self.timeout * 3))
            except ValueError:
                pass
            
            # Prevent core dumps
            try:
                resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
            except ValueError:
                pass
            
            # Limit number of processes
            try:
                resource.setrlimit(resource.RLIMIT_NPROC, (10, 20))
            except ValueError:
                pass
            
            # Set process group (for easier cleanup)
            os.setpgrp()
        
        return preexec
    
    def _monitor_resources(self, process: psutil.Process) -> None:
        """Monitor process resource usage."""
        try:
            while process.is_running():
                try:
                    # Check memory usage
                    memory_info = process.memory_info()
                    memory_mb = memory_info.rss / (1024 * 1024)
                    
                    if memory_mb > self.max_memory_mb:
                        logger.warning(f"Process {process.pid} exceeded memory limit: {memory_mb:.1f} MB")
                        process.terminate()
                        return
                    
                    # Check CPU usage (over last second)
                    cpu_percent = process.cpu_percent()
                    if cpu_percent > self.max_cpu_percent:
                        logger.warning(f"Process {process.pid} exceeded CPU limit: {cpu_percent:.1f}%")
                        # Don't kill immediately for CPU, just warn
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    return
                
                time.sleep(1)  # Check every second
                
        except Exception as e:
            logger.debug(f"Resource monitoring error: {e}")
    
    @contextmanager
    def _create_temp_directory(self):
        """Create temporary directory for sandboxed execution."""
        if not self.sandbox:
            yield None
            return
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set restrictive permissions
            os.chmod(temp_dir, 0o700)
            yield temp_dir


class ContainerWrapper(BaseWrapper):
    """Secure wrapper for Docker containers."""
    
    def __init__(self, container_spec: str, **kwargs):
        super().__init__(**kwargs)
        self.container_spec = container_spec
        
        # Validate container specification
        validate_container_spec(container_spec)
        
        # Prepare Docker command
        self._docker_command = self._prepare_docker_command()
    
    def _prepare_docker_command(self) -> List[str]:
        """Prepare Docker command with security constraints."""
        # Parse existing command
        parts = shlex.split(self.container_spec)
        
        if not parts or parts[0] != 'docker':
            raise WrapperError("Container spec must start with 'docker'")
        
        if len(parts) < 3 or parts[1] != 'run':
            raise WrapperError("Container spec must use 'docker run'")
        
        # Add security flags
        security_flags = [
            '--rm',  # Remove container after execution
            '--interactive',  # Keep stdin open
            '--read-only',  # Make filesystem read-only
            '--tmpfs', '/tmp:rw,noexec,nosuid,size=100m',  # Writable temp with limits
            '--memory', f'{self.max_memory_mb}m',  # Memory limit
            '--cpus', str(self.max_cpu_percent / 100),  # CPU limit
            '--user', 'nobody',  # Run as non-root user
            '--no-new-privileges',  # Prevent privilege escalation
            '--cap-drop', 'ALL',  # Drop all capabilities
        ]
        
        # Network restrictions
        if not self.allow_network:
            security_flags.extend(['--network', 'none'])
        
        # Insert security flags after 'docker run'
        secure_command = parts[:2] + security_flags + parts[2:]
        
        return secure_command
    
    def create_agent_function(self) -> AgentFunction:
        """Create the agent function."""
        def container_agent(message: str) -> str:
            return self._execute_with_retries(message)
        
        return container_agent
    
    def _execute_with_retries(self, message: str) -> str:
        """Execute container with retry logic."""
        last_error = None
        
        for attempt in range(self.retries + 1):
            try:
                return self._execute_container(message)
            except Exception as e:
                last_error = e
                if attempt < self.retries:
                    logger.warning(f"Container attempt {attempt + 1} failed, retrying: {e}")
                    time.sleep(min(2 ** attempt, 10))  # Exponential backoff
                else:
                    logger.error(f"All container attempts failed")
        
        raise WrapperError(f"Container execution failed after {self.retries + 1} attempts: {last_error}")
    
    def _execute_container(self, message: str) -> str:
        """Execute Docker container securely."""
        try:
            process = subprocess.Popen(
                self._docker_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            
            # Monitor the process
            psutil_process = psutil.Process(process.pid)
            self._register_process(psutil_process)
            
            try:
                stdout, stderr = process.communicate(
                    input=message,
                    timeout=self.timeout
                )
                
                if process.returncode != 0:
                    raise WrapperError(f"Container failed with exit code {process.returncode}: {stderr}")
                
                return stdout.strip()
            
            finally:
                self._unregister_process(process.pid)
                
                # Ensure container is stopped
                if process.poll() is None:
                    try:
                        process.terminate()
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
        
        except subprocess.TimeoutExpired:
            raise ResourceLimitExceededError(f"Container timed out after {self.timeout} seconds")
        except Exception as e:
            if isinstance(e, WrapperError):
                raise
            raise WrapperError(f"Container execution failed: {e}")


class SecurityWrapper(BaseWrapper):
    """Security wrapper for functions and framework instances."""
    
    def __init__(self, target: Any, config: Dict[str, Any]):
        super().__init__(
            timeout=config.get('timeout', 120),
            retries=config.get('retries', 0),
            max_memory_mb=config.get('max_memory_mb', 1024),
            max_cpu_percent=config.get('max_cpu_percent', 50),
            allow_network=config.get('allow_network', True),
            sandbox=config.get('sandbox', False),
        )
        self.target = target
        self.config = config
    
    def create_agent_function(self) -> AgentFunction:
        """Create secured agent function."""
        if callable(self.target):
            return self._wrap_callable()
        else:
            return self._wrap_framework_instance()
    
    def _wrap_callable(self) -> AgentFunction:
        """Wrap a callable with security constraints."""
        def secure_callable(message: str) -> Union[str, Generator[str, None, None]]:
            # Set up resource monitoring
            start_time = time.time()
            
            try:
                # Execute with timeout
                if asyncio.iscoroutinefunction(self.target):
                    # Async function
                    return self._execute_async_secure(message, start_time)
                else:
                    # Sync function
                    return self._execute_sync_secure(message, start_time)
                    
            except Exception as e:
                if isinstance(e, (ResourceLimitExceededError, SecurityWrapperError)):
                    raise
                raise SecurityWrapperError(f"Secure execution failed: {e}")
        
        return secure_callable
    
    def _execute_sync_secure(self, message: str, start_time: float) -> Union[str, Generator[str, None, None]]:
        """Execute synchronous function with security."""
        # Check timeout periodically for generators
        def timeout_checker():
            while time.time() - start_time < self.timeout:
                time.sleep(0.1)
            raise ResourceLimitExceededError(f"Function execution timed out after {self.timeout} seconds")
        
        timeout_thread = threading.Thread(target=timeout_checker, daemon=True)
        timeout_thread.start()
        
        try:
            result = self.target(message)
            
            # Handle different return types
            if hasattr(result, '__iter__') and not isinstance(result, str):
                # Generator - wrap with timeout checks
                return self._secure_generator(result, start_time)
            else:
                return str(result)
                
        except Exception as e:
            raise SecurityWrapperError(f"Function execution failed: {e}")
    
    def _execute_async_secure(self, message: str, start_time: float):
        """Execute async function with security (placeholder)."""
        # For now, just call it - full async support would need more work
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're already in an async context
                raise SecurityWrapperError("Async execution in async context not yet supported")
            else:
                return asyncio.run(self.target(message))
        except Exception as e:
            raise SecurityWrapperError(f"Async function execution failed: {e}")
    
    def _secure_generator(self, generator, start_time: float) -> Generator[str, None, None]:
        """Wrap generator with timeout and resource checks."""
        try:
            for item in generator:
                # Check timeout
                if time.time() - start_time > self.timeout:
                    raise ResourceLimitExceededError(f"Generator timed out after {self.timeout} seconds")
                
                yield str(item)
                
        except Exception as e:
            if isinstance(e, ResourceLimitExceededError):
                raise
            raise SecurityWrapperError(f"Generator execution failed: {e}")
    
    def _wrap_framework_instance(self) -> AgentFunction:
        """Wrap framework instance (placeholder)."""
        # This would wrap framework-specific methods with security
        # For now, return the instance as-is
        return self.target


# Export main classes
__all__ = [
    'BaseWrapper',
    'ProcessWrapper',
    'ContainerWrapper',
    'SecurityWrapper',
    'WrapperError',
    'SecurityWrapperError',
    'ResourceLimitExceededError',
]