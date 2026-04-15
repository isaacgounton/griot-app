"""Agent listing and detail endpoints."""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends

from app.services.agents.agent_service import agent_service
from app.utils.auth import get_current_user

# Main agents router - endpoints for listing and getting agent details.
# Using an empty string prefix keeps routes rooted at /api/v1/agents when mounted.
router = APIRouter(tags=["Agents"])


@router.get("/", response_model=List[Dict[str, Any]])
async def list_agents(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get list of all available agents.

    Returns:
        List of available agents with their details
    """
    try:
        return await agent_service.get_available_agents()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agents: {str(e)}"
        )
@router.get("/{agent_type}", response_model=Dict[str, Any])
async def get_agent_details(agent_type: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get detailed information about a specific agent.

    Args:
        agent_type: The type of agent

    Returns:
        Agent details
    """
    try:
        agent_details = await agent_service.get_agent_details(agent_type)
        if not agent_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent type '{agent_type}' not found"
            )
        return agent_details
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent details: {str(e)}"
        )


__all__ = ["router"]
