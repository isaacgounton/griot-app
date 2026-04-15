#!/usr/bin/env python3
"""
API Endpoint Discovery Utility

Scans the FastAPI application routes and generates a comprehensive report
of all available endpoints organized by category.

Usage:
    python discover_endpoints.py [--output FILE] [--verbose]
"""

import os
import sys
import ast
import inspect
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
import argparse


class EndpointInfo:
    """Information about a single endpoint."""

    def __init__(self, path: str, method: str, handler_name: str, file_path: str, summary: str = ""):
        self.path = path
        self.method = method
        self.handler_name = handler_name
        self.file_path = file_path
        self.summary = summary


class RouteCategory:
    """Information about a route category."""

    def __init__(self, name: str, path: str, router_prefix: str = ""):
        self.name = name
        self.path = path
        self.router_prefix = router_prefix
        self.endpoints: List[EndpointInfo] = []


class EndpointDiscovery:
    """Discovers and analyzes FastAPI endpoints."""

    def __init__(self, routes_dir: str = "app/routes"):
        self.routes_dir = Path(routes_dir)
        self.categories: Dict[str, RouteCategory] = {}
        self.total_endpoints = 0

    def discover_routes(self) -> None:
        """Discover all route categories and their endpoints."""
        if not self.routes_dir.exists():
            print(f"❌ Routes directory not found: {self.routes_dir}")
            return

        # Find all route directories
        route_dirs = []
        for item in self.routes_dir.iterdir():
            if item.is_dir() and not item.name.startswith('__'):
                route_dirs.append(item)

        print(f"📁 Found {len(route_dirs)} route categories")

        for route_dir in sorted(route_dirs):
            category_name = route_dir.name
            print(f"🔍 Analyzing category: {category_name}")

            category = RouteCategory(
                name=category_name,
                path=str(route_dir)
            )

            # Find __init__.py or router files
            init_file = route_dir / "__init__.py"
            if init_file.exists():
                self._analyze_init_file(init_file, category)
            else:
                # Look for individual router files
                for py_file in route_dir.glob("*.py"):
                    if py_file.name != "__init__.py":
                        self._analyze_router_file(py_file, category)

            if category.endpoints:
                self.categories[category_name] = category
                self.total_endpoints += len(category.endpoints)
                print(f"   ✅ Found {len(category.endpoints)} endpoints")

    def _analyze_init_file(self, file_path: Path, category: RouteCategory) -> None:
        """Analyze a route __init__.py file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse the AST to find router includes
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module and 'router' in content.lower():
                        # Look for router imports
                        for alias in node.names:
                            if 'router' in alias.name.lower():
                                # Try to find the actual router file
                                router_file = file_path.parent / f"{alias.name.replace('_router', '')}.py"
                                if router_file.exists():
                                    self._analyze_router_file(router_file, category)
                                else:
                                    # Look for any .py file that might contain routes
                                    for py_file in file_path.parent.glob("*.py"):
                                        if py_file != file_path:
                                            self._analyze_router_file(py_file, category)
                                            break

        except Exception as e:
            print(f"   ⚠️  Error analyzing {file_path}: {e}")

    def _analyze_router_file(self, file_path: Path, category: RouteCategory) -> None:
        """Analyze a router file to extract endpoints."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse the AST
            tree = ast.parse(content)

            router_prefix = ""
            current_router = None

            for node in ast.walk(tree):
                # Find APIRouter instantiation
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == 'router':
                            if isinstance(node.value, ast.Call):
                                # Check if it's APIRouter
                                if hasattr(node.value.func, 'id') and node.value.func.id == 'APIRouter':
                                    # Extract prefix if available
                                    for kwarg in node.value.keywords:
                                        if kwarg.arg == 'prefix' and isinstance(kwarg.value, ast.Str):
                                            router_prefix = kwarg.value.s
                                            break
                                elif hasattr(node.value.func, 'attr') and node.value.func.attr == 'APIRouter':
                                    # From fastapi import
                                    for kwarg in node.value.keywords:
                                        if kwarg.arg == 'prefix' and isinstance(kwarg.value, ast.Str):
                                            router_prefix = kwarg.value.s
                                            break

                # Find route decorators
                elif isinstance(node, ast.FunctionDef):
                    decorator_names = []
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Call):
                            if hasattr(decorator.func, 'attr'):
                                decorator_names.append(decorator.func.attr)
                            elif hasattr(decorator.func, 'id'):
                                decorator_names.append(decorator.func.id)

                    # Check for HTTP method decorators
                    http_methods = ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']
                    for decorator in decorator_names:
                        if decorator.lower() in http_methods:
                            # Extract path from decorator arguments
                            path = ""
                            if isinstance(node, ast.FunctionDef) and node.decorator_list:
                                for decorator in node.decorator_list:
                                    if isinstance(decorator, ast.Call) and decorator.args:
                                        if isinstance(decorator.args[0], ast.Str):
                                            path = decorator.args[0].s
                                            break

                            if path or decorator.lower() in ['get', 'post', 'put', 'delete']:
                                # Create endpoint info
                                method = decorator.upper()
                                handler_name = node.name
                                summary = self._extract_docstring(node)

                                endpoint = EndpointInfo(
                                    path=path if path else f"/{handler_name}",
                                    method=method,
                                    handler_name=handler_name,
                                    file_path=str(file_path),
                                    summary=summary
                                )

                                category.endpoints.append(endpoint)

            # Update category router prefix if found
            if router_prefix and not category.router_prefix:
                category.router_prefix = router_prefix

        except Exception as e:
            print(f"   ⚠️  Error analyzing {file_path}: {e}")

    def _extract_docstring(self, node: ast.FunctionDef) -> str:
        """Extract docstring from a function node."""
        if node.body and isinstance(node.body[0], ast.Expr):
            if isinstance(node.body[0].value, ast.Str):
                return node.body[0].value.s.strip()
        return ""

    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate a comprehensive report of discovered endpoints."""
        report_lines = [
            "# API Endpoint Discovery Report",
            "",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "## Summary",
            f"- Total Categories: {len(self.categories)}",
            f"- Total Endpoints: {self.total_endpoints}",
            ""
        ]

        # Sort categories
        sorted_categories = sorted(self.categories.keys())

        for category_name in sorted_categories:
            category = self.categories[category_name]

            report_lines.extend([
                f"## Category: {category_name}",
                f"- Path: {category.path}",
                f"- Router Prefix: {category.router_prefix}",
                f"- Endpoints: {len(category.endpoints)}",
                "",
                "### Endpoints"
            ])

            for endpoint in category.endpoints:
                report_lines.extend([
                    f"- **{endpoint.method}** `{endpoint.path}`",
                    f"  - Handler: `{endpoint.handler_name}` in `{endpoint.file_path}`",
                    f"  - Summary: {endpoint.summary}" if endpoint.summary else "  - Summary: [No summary available]",
                    ""
                ])

        report = "\n".join(report_lines)

        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"📄 Report saved to: {output_path}")

        return report

    def print_summary(self) -> None:
        """Print a summary of discovered endpoints."""
        print("
📊 Discovery Summary:"        print(f"   Categories: {len(self.categories)}")
        print(f"   Total Endpoints: {self.total_endpoints}")

        for name, category in sorted(self.categories.items()):
            print(f"   - {name}: {len(category.endpoints)} endpoints")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Discover API endpoints")
    parser.add_argument("--routes-dir", default="app/routes", help="Routes directory to scan")
    parser.add_argument("--output", "-o", default="temp/endpoint_discovery_report.md", help="Output file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    print("🔍 Starting API Endpoint Discovery...")

    discovery = EndpointDiscovery(args.routes_dir)
    discovery.discover_routes()

    if discovery.categories:
        discovery.print_summary()
        report = discovery.generate_report(args.output)
        print("✅ Discovery completed successfully")
    else:
        print("❌ No endpoints discovered")
        sys.exit(1)


if __name__ == "__main__":
    main()