#!/usr/bin/env python3
"""
Validate requirements files for common issues and best practices.
"""

import re
import sys
from pathlib import Path
import subprocess
import glob

def check_pinned_versions(requirements_file):
    """Check for properly pinned versions."""
    issues = []
    
    with open(requirements_file, 'r') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines, 1):
        line = line.strip()
        if line and not line.startswith('#'):
            # Check for unpinned packages (no version specifier)
            if '==' not in line and '>=' not in line and '~=' not in line and '<' not in line:
                issues.append(f"Line {i}: '{line}' has no version constraint")
            
            # Check for overly broad constraints
            if line.count('>=') > 0 and '<' not in line and '~=' not in line:
                # Allow some exceptions for stable packages
                package_name = line.split('>=')[0].strip()
                if package_name not in ['fastapi', 'uvicorn', 'pydantic']:
                    issues.append(f"Line {i}: '{line}' has overly broad version constraint (consider adding upper bound)")
    
    return issues

def check_security_packages(requirements_file):
    """Check for known insecure packages."""
    insecure_packages = [
        'django<3.2',
        'flask<2.0',
        'requests<2.20',
        'urllib3<1.24.2',
        'pyyaml<5.1',
        'jinja2<2.10.1'
    ]
    
    issues = []
    
    with open(requirements_file, 'r') as f:
        content = f.read()
    
    for insecure in insecure_packages:
        if insecure in content:
            issues.append(f"Potentially insecure package version: {insecure}")
    
    return issues

def check_duplicate_packages(requirements_files):
    """Check for duplicate package declarations across all requirements files."""
    packages = {}
    issues = []
    
    for req_file in requirements_files:
        with open(req_file, 'r') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if line and not line.startswith('#'):
                # Extract package name
                package_name = re.split(r'[>=<~!]', line)[0].strip()
                location = f"{req_file.name}:{i}"
                if package_name in packages:
                    issues.append(f"Duplicate package '{package_name}' in {packages[package_name]} and {location}")
                else:
                    packages[package_name] = location
    
    return issues

def check_format_consistency(requirements_file):
    """Check for consistent formatting."""
    issues = []
    
    with open(requirements_file, 'r') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines, 1):
        line = line.strip()
        if line and not line.startswith('#'):
            # Check for spaces around operators
            if ' >= ' in line or ' == ' in line or ' <= ' in line:
                issues.append(f"Line {i}: Inconsistent spacing around version operators")
            
            # Check for mixed case in package names
            package_name = re.split(r'[>=<~!]', line)[0].strip()
            if package_name != package_name.lower():
                issues.append(f"Line {i}: Package name '{package_name}' should be lowercase")
    
    return issues

def validate_installability(requirements_files):
    """Test if requirements can be installed."""
    print("🧪 Testing package installability...")
    
    try:
        # Create a temporary virtual environment
        result = subprocess.run([
            'python', '-m', 'venv', 'temp_validation_env'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            return [f"Failed to create test environment: {result.stderr}"]
        
        # Try to install all requirements files
        install_args = ['temp_validation_env/bin/pip', 'install']
        for req_file in requirements_files:
            install_args.extend(['-r', str(req_file)])
        
        result = subprocess.run(install_args, capture_output=True, text=True, timeout=600)
        
        # Clean up
        subprocess.run(['rm', '-rf', 'temp_validation_env'])
        
        if result.returncode != 0:
            return [f"Failed to install requirements: {result.stderr}"]
        
        return []
        
    except subprocess.TimeoutExpired:
        subprocess.run(['rm', '-rf', 'temp_validation_env'])
        return ["Installation test timed out (>10 minutes)"]
    except Exception as e:
        subprocess.run(['rm', '-rf', 'temp_validation_env'])
        return [f"Installation test failed: {str(e)}"]

def main():
    """Main validation function."""
    # Find all requirements files
    requirements_files = list(Path('.').glob('requirements-*.txt'))
    
    if not requirements_files:
        print("❌ No requirements-*.txt files found!")
        sys.exit(1)
    
    print(f"🔍 Validating {len(requirements_files)} requirements files: {[f.name for f in requirements_files]}")
    
    all_issues = []
    
    # Check for duplicate packages across all files
    print("   • Cross-file Duplicate Packages...")
    dup_issues = check_duplicate_packages(requirements_files)
    if dup_issues:
        all_issues.extend([f"[Duplicates] {issue}" for issue in dup_issues])
    else:
        print("     ✅ No duplicate packages found")
    
    # Run checks on each file
    for req_file in requirements_files:
        print(f"   • Validating {req_file.name}...")
        
        file_issues = []
        
        checks = [
            ("Version Pinning", check_pinned_versions),
            ("Security Packages", check_security_packages),
            ("Format Consistency", check_format_consistency),
        ]
        
        for check_name, check_func in checks:
            issues = check_func(req_file)
            if issues:
                file_issues.extend([f"[{req_file.name} - {check_name}] {issue}" for issue in issues])
            else:
                print(f"     ✅ {check_name} passed")
        
        all_issues.extend(file_issues)
    
    # Test installability (optional, can be slow)
    if '--test-install' in sys.argv:
        print("   • Installation Test...")
        install_issues = validate_installability(requirements_files)
        if install_issues:
            all_issues.extend([f"[Installation] {issue}" for issue in install_issues])
        else:
            print("     ✅ Installation test passed")
    
    # Report results
    if all_issues:
        print(f"\n❌ Found {len(all_issues)} issues:")
        for issue in all_issues:
            print(f"   • {issue}")
        
        # Check if any are critical
        critical_keywords = ['security', 'insecure', 'duplicate', 'failed']
        critical_issues = [issue for issue in all_issues 
                          if any(keyword in issue.lower() for keyword in critical_keywords)]
        
        if critical_issues:
            print(f"\n🚨 {len(critical_issues)} critical issues found!")
            sys.exit(1)
        else:
            print("\n⚠️ Issues found but none are critical.")
            sys.exit(0)
    else:
        print("\n✅ All validation checks passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()
