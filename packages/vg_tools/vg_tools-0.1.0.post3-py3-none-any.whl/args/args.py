import argparse
import os
from dataclasses import dataclass
from typing import List, Optional
import logging

@dataclass
class ParsedArgs:
    php_version: str
    provisioned_ip: Optional[List[str]]
    extra_vars: str
    ssh_key_file: str
    ssh_password: str
    ssh_user: str
    ssh_pub_key_file: str
    log_level: int

def parse_log_level(level_str: str) -> int:
    """Convert logging level from string to numeric value."""
    # level_str should be like 'INFO', 'WARNING', 'ERROR', etc.
    level_str = level_str.upper()
    if hasattr(logging, level_str):
        return getattr(logging, level_str)
    print(f"Unknown log level: {level_str}, fallback to default logging level WARNING")
    return logging.WARNING

def parse_args() -> ParsedArgs:
    parser = argparse.ArgumentParser(description="Provision and deploy with dynamic IP and PHP version.")
    parser.add_argument("--ssh-key-file", default="~/.ssh/id_rsa", help="Path to SSH key file, default ~/.ssh/id_rsa")
    parser.add_argument("--php-version", default="8.1", help="Override PHP version (default 8.1)")
    parser.add_argument("--provisioned-ip", nargs="+", default=None, help="Provide one or more provisioned IPs directly (skip terraform output)")
    parser.add_argument("--extra-vars", default="", help="Extra vars for ansible-playbook")
    parser.add_argument("--ssh-password", default="", help="Using password for SSH connection")
    parser.add_argument("--ssh-user", default="root", help="User for SSH connection (default root user)")
    parser.add_argument("--ssh-pub-key-file", default="~/.ssh/id_rsa.pub", help="Path to SSH public key file, default ~/.ssh/id_rsa.pub")
    parser.add_argument("--log-level", default="WARNING", help="Logging level (default WARNING)")

    args = parser.parse_args()
    ssh_key_file = os.path.expanduser(args.ssh_key_file)
    if not os.path.isfile(ssh_key_file):
        print(f"WARN: SSH key file does not exist: {ssh_key_file}, try to check password!")
        if not args.ssh_password or args.ssh_password == "":
            print("WARN: SSH password is empty!")
            print("ERROR: At least one of SSH key file or password must be provided.")
            raise SystemExit(1)

    return ParsedArgs(
        php_version=args.php_version,
        provisioned_ip=args.provisioned_ip,
        extra_vars=args.extra_vars,
        ssh_key_file=args.ssh_key_file,
        ssh_password=args.ssh_password,
        ssh_user=args.ssh_user,
        ssh_pub_key_file=args.ssh_pub_key_file,
        log_level=parse_log_level(args.log_level)
    )
