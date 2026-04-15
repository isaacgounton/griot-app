"""Service for secure Python code execution with AST-based validation and resource limits."""

import ast
import json
import logging
import os
import subprocess
import tempfile
import textwrap
import time
from typing import Any

from app.models import JobType
from app.services.job_queue import job_queue

logger = logging.getLogger(__name__)

# --- Security constants ---

BLOCKED_MODULES = frozenset({
    "os", "subprocess", "sys", "socket", "urllib", "requests", "http",
    "ftplib", "smtplib", "threading", "multiprocessing", "signal",
    "ctypes", "importlib", "shutil", "pathlib", "glob", "tempfile",
    "builtins", "gc", "inspect", "pickle", "shelve", "marshal",
    "resource", "pty", "pipes", "select", "mmap", "webbrowser",
    "code", "codeop", "compileall", "antigravity", "turtle",
    "asyncio", "concurrent", "xmlrpc", "pdb", "profile", "cProfile",
})

BLOCKED_FUNCTIONS = frozenset({
    "eval", "exec", "compile", "open", "__import__", "input",
    "breakpoint", "exit", "quit", "globals", "locals", "vars",
    "dir", "getattr", "setattr", "delattr", "hasattr",
    "memoryview",
})

BLOCKED_ATTRS = frozenset({
    "__import__", "__subclasses__", "__bases__", "__mro__",
    "__class__", "__globals__", "__code__", "__builtins__",
    "__loader__", "__spec__", "__qualname__",
})

SAFE_DUNDERS = frozenset({
    "__init__", "__str__", "__repr__", "__len__", "__iter__",
    "__next__", "__getitem__", "__setitem__", "__delitem__",
    "__contains__", "__eq__", "__ne__", "__lt__", "__gt__",
    "__le__", "__ge__", "__add__", "__radd__", "__sub__", "__mul__",
    "__rmul__", "__truediv__", "__floordiv__", "__mod__", "__pow__",
    "__neg__", "__pos__", "__abs__", "__bool__", "__int__",
    "__float__", "__hash__", "__enter__", "__exit__",
    "__name__", "__doc__", "__dict__", "__slots__",
    "__call__", "__format__", "__index__",
})

# Unique placeholder that won't collide with Python code
_CODE_PLACEHOLDER = "### __USER_CODE_HERE__ ###"

_EXECUTION_TEMPLATE = f'''\
import sys
import json
from io import StringIO
import contextlib

_blocked = set((
    'eval', 'exec', 'compile', '__import__', 'open', 'input',
    'breakpoint', 'exit', 'quit', 'globals', 'locals', 'vars',
    'dir', 'getattr', 'setattr', 'delattr', 'hasattr',
    'memoryview', 'type',
))
_safe = dict((k, v) for k, v in __builtins__.__dict__.items() if k not in _blocked)

@contextlib.contextmanager
def _capture():
    out, err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = out, err
        yield out, err
    finally:
        sys.stdout, sys.stderr = old_out, old_err

def _user_code():
{_CODE_PLACEHOLDER}

with _capture() as (_out, _err):
    try:
        _rv = _user_code()
    except Exception as _e:
        print(type(_e).__name__ + ": " + (str(_e) or "no details"), file=sys.stderr)
        _rv = None

_result = dict(
    stdout=_out.getvalue(),
    stderr=_err.getvalue(),
    return_value=_rv,
)
print(json.dumps(_result, default=str))
'''


class CodeExecutionService:
    """Secure Python code execution with AST validation and resource limits."""

    def _validate_code(self, code: str) -> tuple[bool, str]:
        """Validate code using AST analysis. Returns (is_valid, error_message)."""
        if not code or not code.strip():
            return False, "Code cannot be empty"
        if len(code) > 10_000:
            return False, "Code too long (maximum 10KB)"

        try:
            tree = ast.parse(code, mode="exec")
        except SyntaxError as e:
            return False, f"Syntax error on line {e.lineno}: {e.msg}"

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    if root in BLOCKED_MODULES:
                        return False, f"Blocked import '{alias.name}' on line {node.lineno}"

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root = node.module.split(".")[0]
                    if root in BLOCKED_MODULES:
                        return False, f"Blocked import from '{node.module}' on line {node.lineno}"

            elif isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id in BLOCKED_FUNCTIONS:
                    return False, f"Blocked function '{func.id}()' on line {node.lineno}"
                if isinstance(func, ast.Attribute) and func.attr in BLOCKED_ATTRS:
                    return False, f"Blocked attribute access '.{func.attr}' on line {node.lineno}"

            elif isinstance(node, ast.Attribute):
                if node.attr in BLOCKED_ATTRS:
                    return False, f"Blocked attribute '.{node.attr}' on line {node.lineno}"
                if (
                    node.attr.startswith("__")
                    and node.attr.endswith("__")
                    and node.attr not in SAFE_DUNDERS
                ):
                    return False, f"Blocked dunder access '.{node.attr}' on line {node.lineno}"

        return True, ""

    @staticmethod
    def _get_preexec_fn(memory_mb: int = 256, cpu_seconds: int = 30, fsize_mb: int = 10):
        """Return a preexec_fn that sets resource limits for the child process."""
        def _set_limits():
            import resource as _res
            mem = memory_mb * 1024 * 1024
            _res.setrlimit(_res.RLIMIT_AS, (mem, mem))
            _res.setrlimit(_res.RLIMIT_CPU, (cpu_seconds, cpu_seconds + 5))
            fsize = fsize_mb * 1024 * 1024
            _res.setrlimit(_res.RLIMIT_FSIZE, (fsize, fsize))
            _res.setrlimit(_res.RLIMIT_NPROC, (0, 0))
        return _set_limits

    async def execute_python(self, job_id: str, code: str, timeout: int = 30) -> dict[str, Any]:
        """Queue a Python code execution job."""
        if not isinstance(timeout, int) or timeout < 1 or timeout > 300:
            timeout = 30

        is_valid, error_msg = self._validate_code(code)
        if not is_valid:
            return {"error": error_msg, "job_id": job_id}

        params = {"code": code, "timeout": timeout}

        async def process_wrapper(_job_id: str, data: dict[str, Any]) -> dict[str, Any]:
            return await self.process_python_execution(data)

        await job_queue.add_job(
            job_id=job_id,
            job_type=JobType.CODE_EXECUTION,
            process_func=process_wrapper,
            data=params,
        )
        return {"job_id": job_id}

    async def process_python_execution(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute Python code in a restricted subprocess."""
        temp_file_path = None
        try:
            code = params["code"]
            timeout = params.get("timeout", 30)

            indented_code = textwrap.indent(code, "    ")
            final_code = _EXECUTION_TEMPLATE.replace(_CODE_PLACEHOLDER, indented_code)

            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                temp_file_path = f.name
                f.write(final_code)
                f.flush()

            logger.debug("Executing code in %s", temp_file_path)
            start = time.monotonic()

            try:
                result = subprocess.run(
                    ["python3", temp_file_path],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    preexec_fn=self._get_preexec_fn(
                        memory_mb=256,
                        cpu_seconds=timeout,
                        fsize_mb=10,
                    ),
                    env={
                        "PATH": "/usr/bin:/bin",
                        "HOME": "/tmp",
                        "LANG": "en_US.UTF-8",
                    },
                )
            except subprocess.TimeoutExpired:
                return {
                    "stdout": "",
                    "stderr": f"Execution timed out after {timeout} seconds",
                    "exit_code": 124,
                    "result": None,
                    "execution_time": round(time.monotonic() - start, 3),
                }
            except subprocess.SubprocessError as e:
                return {
                    "stdout": "",
                    "stderr": f"Execution failed: {e}",
                    "exit_code": 1,
                    "result": None,
                    "execution_time": round(time.monotonic() - start, 3),
                }

            elapsed = round(time.monotonic() - start, 3)

            try:
                output = json.loads(result.stdout)
                return {
                    "result": output.get("return_value"),
                    "stdout": output.get("stdout", ""),
                    "stderr": output.get("stderr", ""),
                    "exit_code": result.returncode,
                    "execution_time": elapsed,
                }
            except json.JSONDecodeError:
                return {
                    "result": None,
                    "stdout": result.stdout,
                    "stderr": result.stderr or "Failed to parse execution output",
                    "exit_code": result.returncode,
                    "execution_time": elapsed,
                }

        except Exception as e:
            logger.error("Error processing code execution: %s", e)
            raise
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass


code_execution_service = CodeExecutionService()
