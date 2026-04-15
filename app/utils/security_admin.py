"""
Security administration utilities for managing IP blocks and monitoring.
"""
import logging
from typing import Set, Dict, List
import json
import os
import time

logger = logging.getLogger(__name__)

class SecurityAdmin:
    """Admin utilities for security management"""
    
    def __init__(self, blocked_ips_file: str = "data/blocked_ips.json"):
        self.blocked_ips_file = blocked_ips_file
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        """Ensure data directory exists"""
        os.makedirs(os.path.dirname(self.blocked_ips_file), exist_ok=True)
    
    def load_persistent_blocks(self) -> Set[str]:
        """Load permanently blocked IPs from file"""
        try:
            if os.path.exists(self.blocked_ips_file):
                with open(self.blocked_ips_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('blocked_ips', []))
        except Exception as e:
            logger.error(f"Error loading blocked IPs: {e}")
        return set()
    
    def save_persistent_blocks(self, blocked_ips: Set[str]):
        """Save permanently blocked IPs to file"""
        try:
            data = {
                'blocked_ips': list(blocked_ips),
                'last_updated': time.time()
            }
            with open(self.blocked_ips_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(blocked_ips)} permanently blocked IPs")
        except Exception as e:
            logger.error(f"Error saving blocked IPs: {e}")
    
    def block_ip_permanently(self, ip: str, reason: str = "Manual block"):
        """Permanently block an IP address"""
        blocked_ips = self.load_persistent_blocks()
        blocked_ips.add(ip)
        self.save_persistent_blocks(blocked_ips)
        logger.warning(f"IP {ip} permanently blocked: {reason}")
        return True
    
    def unblock_ip(self, ip: str):
        """Remove an IP from permanent block list"""
        blocked_ips = self.load_persistent_blocks()
        if ip in blocked_ips:
            blocked_ips.remove(ip)
            self.save_persistent_blocks(blocked_ips)
            logger.info(f"IP {ip} unblocked")
            return True
        return False
    
    def list_blocked_ips(self) -> List[str]:
        """Get list of permanently blocked IPs"""
        return list(self.load_persistent_blocks())
    
    def analyze_attack_patterns(self, log_file: str = "logs/app.log") -> Dict:
        """Analyze attack patterns from logs"""
        patterns = {
            'suspicious_requests': 0,
            'rate_limit_exceeded': 0,
            'blocked_access': 0,
            'top_attacking_ips': {},
            'common_attack_paths': {}
        }
        
        try:
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    for line in f:
                        if 'Suspicious request detected' in line:
                            patterns['suspicious_requests'] += 1
                            # Extract IP from log line
                            if 'IP: ' in line:
                                ip = line.split('IP: ')[1].split(',')[0]
                                patterns['top_attacking_ips'][ip] = patterns['top_attacking_ips'].get(ip, 0) + 1
                        
                        elif 'Rate limit exceeded' in line:
                            patterns['rate_limit_exceeded'] += 1
                        
                        elif 'Blocked IP attempted access' in line:
                            patterns['blocked_access'] += 1
                        
                        elif 'Path: ' in line and 'Suspicious' in line:
                            # Extract attack path
                            path = line.split('Path: ')[1].split(',')[0]
                            patterns['common_attack_paths'][path] = patterns['common_attack_paths'].get(path, 0) + 1
        
        except Exception as e:
            logger.error(f"Error analyzing attack patterns: {e}")
        
        return patterns

# Global instance
security_admin = SecurityAdmin()