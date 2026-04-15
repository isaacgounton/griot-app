"""
Dynamic route discovery and registration utilities for Griot.
Automatically discovers and registers FastAPI routers from the routes directory.
"""
import os
import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from fastapi import APIRouter, FastAPI, Depends
from app.utils.auth import get_current_user
import logging

logger = logging.getLogger(__name__)

# Configuration for route discovery
ROUTE_CONFIG = {
    # Routes that require API key authentication
    "authenticated_routes": [
        "dashboard", "image", "audio", "media", "video", "admin", "agents",
        "ffmpeg", "s3", "code", "conversions", "research", "documents",
        "jobs", "diagnostics", "music", "postiz", "library", "anyllm",
        "pollinations", "mcp", "yt_shorts", "simone", "openai_compat",
        "speaches"
    ],

    # Routes that should be publicly accessible (no API key required)
    "public_routes": [
        "auth"  # only auth routes are public
    ],

    # Routes that should not be auto-discovered (handled manually in main.py)
    "manual_routes": [
        "auth", "admin", "mcp",
        "audio", "media", "video", "pollinations",
        "dashboard", "anyllm", "jobs",
        "chat", "studio", "text", "research"
    ],

    # Routes that should be mounted at specific prefixes
    "route_prefixes": {
        "audio": "/api/v1/audio",
        "media": "/api/v1/media",
        "video": "/api/v1/videos",
        "s3": "/api/v1/s3",
        "library": "/api/v1/library",
        "mcp": None,  # MCP has custom mounting
        "auth": None,  # Auth routes at root level
        "admin": None,  # Admin routes at root level
        "agents": "/api/v1/agents",  # Custom agent routing with API versioning
        "anyllm": "/api/v1",
        "openai_compat": "/api/v1/openai",
        "speaches": "/api/v1/speaches",
    },

    # Custom route configurations
    "custom_mounts": {
        "mcp": {"router": "mcp_router", "no_auth": True, "prefix": None},
        "auth": {"router": "auth_router", "no_auth": True, "prefix": None},
        "admin": {"router": "admin_router", "no_auth": True, "prefix": None},
    }
}

def discover_route_modules(routes_dir: str = "app/routes") -> List[Tuple[str, Path]]:
    """
    Discover all Python modules in the routes directory that contain routers.

    Args:
        routes_dir: Path to the routes directory

    Returns:
        List of tuples (module_name, module_path)
    """
    routes_path = Path(routes_dir)
    discovered_modules = []

    if not routes_path.exists():
        logger.warning(f"Routes directory {routes_dir} does not exist")
        return discovered_modules

    for item in routes_path.rglob("*.py"):
        # Skip private modules (starting with _) but keep __init__.py
        if item.name.startswith("_") and item.name != "__init__.py":
            continue

        # Convert file path to module path
        relative_path = item.relative_to(routes_path)
        module_parts = list(relative_path.with_suffix("").parts)
        module_name = ".".join(module_parts)
        
        # For __init__.py files, the module name should be the package name (without __init__)
        # e.g., documents/__init__.py -> "documents" (package module)
        if item.name == "__init__.py":
            # Remove the __init__ part from module name
            module_parts = module_parts[:-1]  # Remove __init__
            if not module_parts:
                continue  # Skip root __init__.py (app/routes/__init__.py)
            module_name = ".".join(module_parts)
            # Mark it as a package init for special handling
            discovered_modules.append((module_name + ".__init__", item))
        else:
            discovered_modules.append((module_name, item))

    logger.info(f"Discovered {len(discovered_modules)} route modules in {routes_dir}")
    return discovered_modules

def import_router_module(module_name: str) -> Optional[Any]:
    """
    Import a router module by name and return the module object.

    Args:
        module_name: Full module name (e.g., "app.routes.image.generate")

    Returns:
        The imported module or None if import failed
    """
    try:
        module = importlib.import_module(module_name)
        return module
    except ImportError as e:
        logger.warning(f"Failed to import module {module_name}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error importing {module_name}: {e}")
        return None

def extract_router_from_module(module: Any, module_name: str) -> Optional[APIRouter]:
    """
    Extract the FastAPI router from a module.

    Args:
        module: The imported module object
        module_name: Name of the module for logging

    Returns:
        The APIRouter instance or None if not found
    """
    # Look for common router variable names
    router_names = ["router", "api_router", "routes"]

    for name in router_names:
        if hasattr(module, name):
            router = getattr(module, name)
            if isinstance(router, APIRouter):
                logger.info(f"Found router '{name}' in module {module_name}")
                return router

    # If no standard router found, look for any APIRouter instance
    for name, obj in inspect.getmembers(module):
        if isinstance(obj, APIRouter):
            logger.info(f"Found APIRouter '{name}' in module {module_name}")
            return obj

    logger.debug(f"No router found in module {module_name}")
    return None

def determine_route_config(module_name: str, router_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Determine the configuration for mounting a route based on module name and patterns.

    Args:
        module_name: The module name (e.g., "image.generate")
        router_name: Optional router variable name

    Returns:
        Dictionary with route configuration or None when handled manually
    """
    # Extract the category from module name (first part before dot)
    category = module_name.split(".")[0] if "." in module_name else module_name

    # Check if this is a special case module (pollinations, etc.)
    if "pollinations" in module_name:
        base_category = "pollinations"
    else:
        base_category = category

    # Skip routes that are handled manually
    if base_category in ROUTE_CONFIG["manual_routes"]:
        return None

    # Determine if authentication is required
    requires_auth = base_category not in ROUTE_CONFIG["public_routes"]

    # Determine prefix
    prefix = ROUTE_CONFIG["route_prefixes"].get(base_category, "/api/v1")

    # Allow mapping by submodule name too (e.g. image.web_screenshot -> web_screenshot mapping)
    sub_category = module_name.split(".")[-1]
    if sub_category in ROUTE_CONFIG["route_prefixes"]:
        prefix = ROUTE_CONFIG["route_prefixes"][sub_category]

    # Special handling for sub-modules
    if module_name.count(".") > 0:
        # For nested modules like "image.pollinations", use parent category for config
        parent_category = module_name.split(".")[0]
        if parent_category in ROUTE_CONFIG["route_prefixes"]:
            prefix = ROUTE_CONFIG["route_prefixes"][parent_category]

    return {
        "category": base_category,
        "requires_auth": requires_auth,
        "prefix": prefix,
        "module_name": module_name,
        "router_name": router_name
    }

def register_discovered_routes(app: FastAPI, routes_dir: str = "app/routes") -> Dict[str, List[str]]:
    """
    Automatically discover and register all routes from the routes directory.

    Args:
        app: FastAPI application instance
        routes_dir: Path to the routes directory

    Returns:
        Dictionary with registration results
    """
    registration_results = {
        "registered": [],
        "failed": [],
        "skipped": []
    }

    # Discover all route modules
    discovered_modules = discover_route_modules(routes_dir)
    def sort_key(module_entry: Tuple[str, Path]) -> Tuple[str, bool, str]:
        """Group modules by category while ensuring catch-all routers register last."""
        name = module_entry[0]
        parts = name.split(".")
        category = parts[0]
        basename = parts[-1]
        return (category, basename == category, name)

    discovered_modules.sort(key=sort_key)

    def should_skip_nested_module(module_name: str, routes_dir: str) -> bool:
        # If this is a nested module (e.g., documents.to_markdown) and the parent
        # package has an __init__.py that includes routers via include_router(),
        # then the submodule should be included by the parent and we should not
        # register it independently to avoid duplicate route registration.
        # Do not skip the parent package __init__ module itself
        if module_name.endswith('.__init__'):
            return False
        if module_name.count('.') == 0:
            return False
        parent = module_name.split('.')[0]
        parent_init_path = Path(routes_dir) / parent / '__init__.py'
        if parent_init_path.exists():
            try:
                content = parent_init_path.read_text()
                if 'include_router(' in content:
                    return True
            except Exception:
                return False
        return False

    for module_name, module_path in discovered_modules:
        if should_skip_nested_module(module_name, routes_dir):
            logger.debug(f"Skipping nested module {module_name} because parent router includes subrouters")
            registration_results['skipped'].append(f"{module_name} (registered by parent router)")
            continue
        try:
            # Import the module
            # For __init__ modules, import the package itself (without .__init__ suffix)
            if module_name.endswith(".__init__"):
                import_name = module_name[:-9]  # Remove .__init__
                full_module_name = f"app.routes.{import_name}"
            else:
                full_module_name = f"app.routes.{module_name}"
            module = import_router_module(full_module_name)

            if not module:
                registration_results["failed"].append(f"{module_name} (import failed)")
                continue

            # Extract router from module
            router = extract_router_from_module(module, full_module_name)

            if not router:
                registration_results["skipped"].append(f"{module_name} (no router found)")
                continue

            # Determine route configuration
            config = determine_route_config(module_name)

            if config is None:
                registration_results["skipped"].append(f"{module_name} (manual route)")
                continue

            # Prepare dependencies
            dependencies = []
            if config["requires_auth"]:
                dependencies.append(Depends(get_current_user))

            # Handle special custom mounts
            if config["category"] in ROUTE_CONFIG["custom_mounts"]:
                custom_config = ROUTE_CONFIG["custom_mounts"][config["category"]]
                if custom_config["no_auth"]:
                    dependencies = []
                if custom_config["prefix"] is not None:
                    config["prefix"] = custom_config["prefix"]

            # Register the router
            if config["prefix"]:
                app.include_router(
                    router,
                    prefix=config["prefix"],
                    dependencies=dependencies
                )
            else:
                app.include_router(router, dependencies=dependencies)

            registration_results["registered"].append(
                f"{module_name} -> {config['prefix'] or 'root'} (auth: {config['requires_auth']})"
            )

            logger.info(f"✓ Registered route: {module_name} -> {config['prefix'] or 'root'}")

        except Exception as e:
            error_msg = f"{module_name} (error: {str(e)})"
            registration_results["failed"].append(error_msg)
            logger.error(f"✗ Failed to register route {module_name}: {e}")

    # Log summary
    total_discovered = len(discovered_modules)
    total_registered = len(registration_results["registered"])
    total_failed = len(registration_results["failed"])
    total_skipped = len(registration_results["skipped"])

    logger.info(f"Route discovery complete: {total_registered}/{total_discovered} registered, "
                f"{total_failed} failed, {total_skipped} skipped")

    return registration_results

def get_route_summary(registration_results: Dict[str, List[str]]) -> str:
    """
    Generate a human-readable summary of route registration results.

    Args:
        registration_results: Results from register_discovered_routes

    Returns:
        Formatted summary string
    """
    summary_lines = [
        "Route Registration Summary:",
        "=" * 30,
        f"✓ Registered: {len(registration_results['registered'])}",
        f"✗ Failed: {len(registration_results['failed'])}",
        f"⊘ Skipped: {len(registration_results['skipped'])}",
        ""
    ]

    if registration_results["registered"]:
        summary_lines.append("Successfully Registered:")
        for route in registration_results["registered"]:
            summary_lines.append(f"  ✓ {route}")
        summary_lines.append("")

    if registration_results["failed"]:
        summary_lines.append("Failed to Register:")
        for route in registration_results["failed"]:
            summary_lines.append(f"  ✗ {route}")
        summary_lines.append("")

    if registration_results["skipped"]:
        summary_lines.append("Skipped (No Router Found):")
        for route in registration_results["skipped"]:
            summary_lines.append(f"  ⊘ {route}")

    return "\n".join(summary_lines)