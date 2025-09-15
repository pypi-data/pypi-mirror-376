"""A2A-compliant server for Loomdots adapters."""
from __future__ import annotations

from typing import Any, Optional
from starlette.routing import Mount, Route
from starlette.applications import Starlette
from starlette.responses import JSONResponse

from a2a.types import AgentCard
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.apps import A2AStarletteApplication
from a2a.server.agent_execution import AgentExecutor
from a2a.server.request_handlers import DefaultRequestHandler


def get_current_agent_card() -> Optional[AgentCard]:
    """Get the current agent card from the expose module."""
    try:
        # Import here to avoid circular imports
        from .expose import _CURRENT_AGENT_CARD
        return _CURRENT_AGENT_CARD
    except (ImportError, AttributeError):
        return None


def create_app(
    *,
    name: str = "Loomdots Agent",
    description: str = "An A2A-compliant Agent",
    version: str = "1.0.0",
    base_url: Optional[str] = None,
) -> Starlette:
    """
    Create A2A-compliant Starlette application.
    
    Args:
        name: Default agent name if none registered
        description: Default description if none registered  
        version: Default version if none registered
        base_url: Base URL for the agent
        
    Returns:
        Configured Starlette application
    """
    
    # Get agent card from registered agents or create default
    agent_card = get_current_agent_card()
    if agent_card is None:
        from a2a.types import AgentCapabilities
        agent_card = AgentCard(
            name=name,
            description=description,
            version=version,
            url=base_url or "http://localhost:8000",
            capabilities=AgentCapabilities(streaming=True),
            skills=[],
            defaultInputModes=["text"],
            defaultOutputModes=["text"],
        )
    
    # Create A2A components
    task_store = InMemoryTaskStore()
    executor = UniversalAgentExecutor()  # Our custom executor
    request_handler = DefaultRequestHandler(agent_executor=executor, task_store=task_store)
    
    # Build the A2A Starlette app using official SDK
    a2a_server = A2AStarletteApplication(agent_card=agent_card, http_handler=request_handler)
    a2a_app = a2a_server.build()
    
    # Well-known route for agent card
    async def well_known_agent_card(_: Any) -> JSONResponse:
        current_card = get_current_agent_card() or agent_card
        
        if hasattr(current_card, 'model_dump'):
            content = current_card.model_dump()
        elif hasattr(current_card, 'dict'):
            content = current_card.dict()
        else:
            content = current_card
            
        return JSONResponse(content)
    
    # Configure routes - well-known route first to avoid being shadowed
    routes = [
        Route("/.well-known/agent-card.json", endpoint=well_known_agent_card),
        Mount("/", app=a2a_app),
    ]
    
    return Starlette(routes=routes)


class UniversalAgentExecutor(AgentExecutor):
    """
    Universal executor that works with all registered agents.
    
    This executor integrates with the expose module to execute
    the registered agent functions with proper A2A protocol handling.
    """
    
    async def execute(self, context, event_queue) -> None:
        """Execute the registered agent function."""
        from .expose import _REGISTRY_LOCK, _REGISTERED_AGENTS
        from a2a.server.tasks import TaskUpdater
        from a2a.types import TaskState, TextPart, Part
        
        # Validate context
        if not context.task_id or not context.context_id:
            raise ValueError("RequestContext must have task_id and context_id")
        if not context.message:
            raise ValueError("RequestContext must have a message")
        
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        if not context.current_task:
            submit_result = updater.submit()
            if submit_result is not None:
                await submit_result
        start_work_result = updater.start_work()
        if start_work_result is not None:
            await start_work_result
        
        try:
            # Get the registered agent
            with _REGISTRY_LOCK:
                if not _REGISTERED_AGENTS:
                    raise ValueError("No agents registered")
                
                # For now, use the first registered agent
                # TODO: Support multiple agents and routing
                agent_info = next(iter(_REGISTERED_AGENTS.values()))
                agent_function = agent_info.get('wrapped_agent') or agent_info.get('target')
            
            # Get user input
            user_text = context.get_user_input()
            
            # Execute agent function
            if callable(agent_function):
                result = agent_function(user_text)
                
                # Handle different result types
                if hasattr(result, '__aiter__'):
                    # Async generator
                    async for chunk in result:
                        await updater.update_status(
                            TaskState.working,
                            message=updater.new_agent_message([Part(root=TextPart(text=str(chunk)))])
                        )
                elif hasattr(result, '__iter__') and not isinstance(result, str):
                    # Sync generator  
                    for chunk in result:
                        await updater.update_status(
                            TaskState.working,
                            message=updater.new_agent_message([Part(root=TextPart(text=str(chunk)))])
                        )
                else:
                    # Single result
                    await updater.add_artifact([Part(root=TextPart(text=str(result)))])
            else:
                raise ValueError("Registered agent is not callable")
            
            await updater.complete()
            
        except Exception as e:
            from a2a.utils.errors import ServerError
            from a2a.types import InternalError
            raise ServerError(error=InternalError()) from e
    
    async def cancel(self, context, event_queue) -> None:
        """Cancel execution (basic implementation)."""
        from a2a.utils.errors import ServerError
        from a2a.types import UnsupportedOperationError
        # For now, cancellation is not supported
        # TODO: Implement proper cancellation using wrappers
        raise ServerError(error=UnsupportedOperationError())


# Default app instance for uvicorn (created lazily to avoid import issues)
def get_default_app():
    """Get the default app instance for uvicorn."""
    return create_app()

# For uvicorn compatibility
app = None