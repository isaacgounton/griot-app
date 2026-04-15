#!/usr/bin/env python3
"""
Package monitoring script to check for outdated packages and security vulnerabilities.
"""

import subprocess
import json
import sys
from datetime import datetime
from pathlib import Path
import requests

def run_command(cmd):
    """Run a command and return the output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_outdated_packages():
    """Check for outdated packages."""
    print("🔍 Checking for outdated packages...")
    success, stdout, stderr = run_command("pip list --outdated --format=json")
    
    if not success:
        print(f"❌ Error checking outdated packages: {stderr}")
        return []
    
    try:
        outdated = json.loads(stdout)
        if outdated:
            print(f"📦 Found {len(outdated)} outdated packages:")
            for pkg in outdated:
                print(f"  • {pkg['name']}: {pkg['version']} → {pkg['latest_version']}")
        else:
            print("✅ All packages are up to date!")
        return outdated
    except json.JSONDecodeError:
        print("❌ Error parsing outdated packages output")
        return []

def check_security_vulnerabilities():
    """Check for security vulnerabilities."""
    print("\n🔒 Checking for security vulnerabilities...")
    
    # Install safety if not available
    run_command("pip install safety")
    
    success, stdout, stderr = run_command("safety check --json")
    
    if success:
        print("✅ No known security vulnerabilities found!")
        return []
    else:
        try:
            # Parse safety output
            vulnerabilities = json.loads(stderr) if stderr else []
            if vulnerabilities:
                print(f"⚠️ Found {len(vulnerabilities)} security vulnerabilities:")
                for vuln in vulnerabilities:
                    print(f"  • {vuln.get('package', 'Unknown')}: {vuln.get('vulnerability', 'Unknown issue')}")
            return vulnerabilities
        except json.JSONDecodeError:
            print(f"⚠️ Security check completed with warnings: {stderr}")
            return []

def check_package_health():
    """Check overall package health."""
    print("\n💊 Checking package health...")
    
    # Check for conflicting dependencies
    success, stdout, stderr = run_command("pip check")
    
    if success:
        print("✅ No dependency conflicts found!")
    else:
        print(f"⚠️ Dependency conflicts detected:\n{stderr}")
    
    return success

def get_package_info(package_name):
    """Get package information from PyPI."""
    try:
        response = requests.get(f"https://pypi.org/pypi/{package_name}/json", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                'name': data['info']['name'],
                'version': data['info']['version'],
                'summary': data['info']['summary'],
                'last_updated': data['releases'][data['info']['version']][0]['upload_time'] if data['releases'][data['info']['version']] else 'Unknown'
            }
    except Exception as e:
        print(f"⚠️ Could not fetch info for {package_name}: {e}")
    return None

def generate_report(outdated, vulnerabilities):
    """Generate a monitoring report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""
# Package Monitoring Report
**Generated:** {timestamp}

## Summary
- **Outdated packages:** {len(outdated)}
- **Security vulnerabilities:** {len(vulnerabilities)}

## Outdated Packages
"""
    
    if outdated:
        for pkg in outdated:
            report += f"- **{pkg['name']}**: {pkg['version']} → {pkg['latest_version']}\n"
    else:
        report += "✅ All packages are up to date!\n"
    
    report += "\n## Security Vulnerabilities\n"
    
    if vulnerabilities:
        for vuln in vulnerabilities:
            report += f"- **{vuln.get('package', 'Unknown')}**: {vuln.get('vulnerability', 'Unknown issue')}\n"
    else:
        report += "✅ No known security vulnerabilities!\n"
    
    report += f"""
## Recommendations

### High Priority (Security)
{len([v for v in vulnerabilities if 'high' in str(v).lower()])} high-priority security updates needed.

### Medium Priority (Outdated)
{len(outdated)} packages have newer versions available.

### Actions
1. Review security vulnerabilities immediately
2. Test outdated packages in development environment
3. Update packages in batches by category
4. Run full test suite after updates

## Next Steps
```bash
# Update specific packages
pip install --upgrade package_name

# Or use the automated update script
./scripts/update-dependencies.sh --test-only

# For security updates only
pip install --upgrade $(safety check --json | jq -r '.[].package' | tr '\\n' ' ')
```
"""
    
    # Save report
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    report_file = reports_dir / f"package-monitoring-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
    report_file.write_text(report)
    
    print(f"\n📊 Report saved to {report_file}")
    return report_file

def main():
    """Main monitoring function."""
    print("🔍 Starting package monitoring...")
    
    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️ Warning: Not running in a virtual environment")
    
    # Run checks
    outdated = check_outdated_packages()
    vulnerabilities = check_security_vulnerabilities()
    health_ok = check_package_health()
    
    # Generate report
    report_file = generate_report(outdated, vulnerabilities)
    
    # Summary
    print(f"\n📋 Monitoring Summary:")
    print(f"   • Outdated packages: {len(outdated)}")
    print(f"   • Security vulnerabilities: {len(vulnerabilities)}")
    print(f"   • Dependency health: {'✅ Good' if health_ok else '⚠️ Issues'}")
    print(f"   • Report: {report_file}")
    
    # Exit with appropriate code
    if vulnerabilities:
        print("\n🚨 Security vulnerabilities found! Please review and update.")
        sys.exit(1)
    elif outdated:
        print("\n📦 Outdated packages found. Consider updating.")
        sys.exit(0)
    else:
        print("\n✅ All packages are up to date and secure!")
        sys.exit(0)

if __name__ == "__main__":
    main()
