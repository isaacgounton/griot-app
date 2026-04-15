"""
Routes for code execution with enhanced features.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from app.models import CodeExecutionRequest, JobResponse
from app.services.code_execution import code_execution_service
from app.utils.auth import get_current_user
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/code", tags=["System"])

@router.post("/execute/python")
async def execute_python(
    request: CodeExecutionRequest,
    _: Dict[str, Any] = Depends(get_current_user),
):
    """
    Execute Python code.

    Args:
        request: Code execution request with sync parameter

    Returns:
        For sync=True: Direct execution result
        For sync=False: JobResponse with job_id for tracking progress
    """
    try:
        # Handle sync vs async processing
        if request.sync:
            # Validate before execution
            is_valid, error_msg = code_execution_service._validate_code(request.code)
            if not is_valid:
                return {
                    "job_id": None,
                    "status": "completed",
                    "result": {
                        "stdout": "",
                        "stderr": error_msg,
                        "exit_code": 1,
                        "result": None,
                        "execution_time": 0,
                    },
                }
            try:
                result = await code_execution_service.process_python_execution({
                    "code": request.code,
                    "timeout": request.timeout or 30
                })
                logger.info("Completed synchronous Python code execution")
                return {
                    "job_id": None,
                    "status": "completed",
                    "result": result
                }
            except Exception as e:
                logger.error(f"Error in synchronous code execution: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Code execution failed: {str(e)}"
                )
        else:
            # Create async job (existing logic)
            job_id = str(uuid.uuid4())
            result = await code_execution_service.execute_python(
                job_id=job_id,
                code=request.code,
                timeout=request.timeout or 30,
            )
            return JobResponse(job_id=result["job_id"])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create code execution job: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/validate")
async def validate_code(
    code: str,
    timeout: int = 30,
    _: Dict[str, Any] = Depends(get_current_user),
):
    """
    Validate Python code without executing it.

    Checks:
    - Basic syntax errors
    - Dangerous operations
    - Code length limits
    - Timeout validity
    """
    try:
        # Use the service's validation method
        is_valid, error_msg = code_execution_service._validate_code(code)

        # Additional timeout validation
        timeout_valid = isinstance(timeout, int) and 1 <= timeout <= 300

        return {
            "valid": is_valid and timeout_valid,
            "syntax_valid": is_valid,
            "timeout_valid": timeout_valid,
            "error": error_msg if not is_valid else None,
            "code_length": len(code),
            "timeout": timeout,
            "checks": {
                "syntax": is_valid,
                "dangerous_operations": is_valid,  # False if dangerous found
                "length_limit": len(code) <= 10000,
                "timeout_range": timeout_valid
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating code: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Code validation failed: {str(e)}")


