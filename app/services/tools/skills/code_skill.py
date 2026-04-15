"""Code skill — secure Python code execution."""

from typing import Any

from app.services.tools.skills.base import Skill

skill = Skill(name="code", description="Secure Python code execution in a sandbox")


async def _execute_python(args: dict[str, Any]) -> dict[str, Any]:
    from app.services.code_execution.code_execution_service import code_execution_service

    params = {
        "code": args["code"],
        "timeout": args.get("timeout", 30),
    }

    result = await code_execution_service.process_python_execution(params)
    return {
        "stdout": result.get("stdout", ""),
        "stderr": result.get("stderr", ""),
        "result": result.get("result"),
        "exit_code": result.get("exit_code", 0),
        "execution_time": result.get("execution_time"),
    }


skill.action(
    name="execute_python",
    description=(
        "Execute Python code in a secure sandbox and return the output. "
        "Useful for calculations, data processing, and demonstrations. "
        "Some modules are blocked for security (os, subprocess, etc.)."
    ),
    handler=_execute_python,
    properties={
        "code": {
            "type": "string",
            "description": "Python code to execute (max 10KB)",
        },
        "timeout": {
            "type": "integer",
            "description": "Execution timeout in seconds (1-300)",
            "default": 30,
        },
    },
    required=["code"],
)
