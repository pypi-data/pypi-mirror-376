import logging
import os
import subprocess
import sys
import time
from typing import List, Optional, Tuple

from utils.utils import to_absolute_path

logger = logging.getLogger(__name__)


class AnsiblePlaybook:
    def __init__(
        self,
        playbook: str,
        inventory: str,
        working_dir: str,
        private_key_file: str,
        ssh_user: str = "root",
        ssh_password: str = "",
    ):
        """
        Wraps the ansible-playbook CLI.

        :param playbook: Path to the playbook YAML file.
        :param inventory: Path to the inventory file.
        :param working_dir: Path to the working directory.
        :param private_key_file: Private key file
        """
        self.playbook = playbook
        self.inventory = inventory
        self.working_dir = working_dir
        self.private_key_file = private_key_file
        self.ssh_user = ssh_user
        self.ssh_password = ssh_password

    def run(
        self,
        extra_vars: Optional[dict] = None,
        extra_args: Optional[List[str]] = None,
        ssh_common_args: str = "",
        manual_install: bool = False,
    ) -> Tuple[str, str]:
        """
        Run the ansible-playbook command with optional extra arguments.

        :param extra_vars: Dictionary of extra variables (-e key=value).
        :param extra_args: List of extra CLI arguments (e.g., ["-v", "--check"]).
        :return: Combined stdout, stderr output.
        """
        print("Deployment started")
        if not ssh_common_args or ssh_common_args == "":
            ssh_common_args = "-o StrictHostKeyChecking=no"

        cmd = [
            "ansible-playbook",
            "-i",
            self.inventory,
            self.playbook,
            "--ssh-common-args",
            ssh_common_args,
        ]

        # Add extra vars if provided
        if extra_vars:
            for k, v in extra_vars.items():
                cmd.extend(["-e", f"{k}={v}"])
        # Add any additional args
        if extra_args:
            cmd.extend(extra_args)

        # Add private key file or password if provided
        env = os.environ.copy()
        if self.ssh_password and self.ssh_password != "":
            logger.info(f"Using SSH password for user: {self.ssh_user}")
            env["ANSIBLE_SSH_PASSWORD"] = self.ssh_password
            env["ANSIBLE_SSH_USER"] = self.ssh_user
        elif self.private_key_file:
            file = to_absolute_path(self.private_key_file)
            logger.info(f"Using private key file: {file}")
            try:
                with open(file, "r") as f:
                    contents = f.read()
                    if (
                        not contents.strip()
                    ):  # Check for empty or whitespace-only content
                        logger.error(f"Private key file '{file}' is empty.")
                        raise ValueError(f"Private key file '{file}' is empty.")
            except Exception as e:
                logger.error(f"Error reading private key file: {e}")
                raise
            env["ANSIBLE_PRIVATE_KEY_FILE"] = file
            env["ANSIBLE_SSH_USER"] = self.ssh_user

        if manual_install:
            env["SSH_TIMEOUT"] = "60"
        else:
            env["SSH_TIMEOUT"] = "600"
        logger.info(f"Command: {' '.join(cmd)}")
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=self.working_dir,
            bufsize=1,
            env=env,
        )
        # Sequential health check logic: print every 30 seconds until process ends or timeout.
        start_time = time.time()
        timeout = 20 * 60  # 20 minutes
        next_status = start_time + 30

        # stdout_lines, stderr_lines = [], []
        while True:
            if process.poll() is not None:
                break  # Process finished
            now = time.time()
            if now >= next_status:
                print(
                    f"[HealthCheck] Deployment still running at {time.strftime('%X')}"
                )
                next_status = now + 30
            if now - start_time > timeout:
                process.kill()
                stdout, stderr = process.communicate()
                raise RuntimeError(
                    f"Deployment timed out.\nCommand: {' '.join(cmd)}\nStdout:\n{stdout}\nStderr:\n{stderr}"
                )
            time.sleep(10)  # polling interval

        stdout, stderr = process.communicate()
        if process.returncode != 0:
            logger.error(
                f"Deployment failed with exit code {process.returncode}.\n"
                f"Stdout:\n{stdout}\nStderr:\n{stderr}"
            )
            sys.exit(process.returncode)
        # Only get one last line
        stdout_lines = "\n".join(stdout.strip().splitlines()[-1:]) if stdout else ""
        end_time = time.time() - start_time
        print(f"Deployment completed successfully in {end_time:.2f} seconds")
        return stdout_lines, stderr


def construct_inventory(ips, hosts_path: str):
    """Write the IP(s) to the Ansible hosts file with a group header."""
    if isinstance(ips, List):
        with open(hosts_path, "w") as f:
            f.write("[serveradmin]\n")
            for idx, ip in enumerate(ips):
                host = f"pub-ip-serveradmin{idx + 1}"
                # if len(ips) > 1 else "serveradmin"
                f.write(f"{host} ansible_host={ip}\n")
    else:
        for key, inner_dict in ips.items():
            ip = inner_dict["value"]
            with open(hosts_path, "w") as f:
                f.write("[serveradmin]\n")
                f.write(f"{key} ansible_host={ip}\n")
