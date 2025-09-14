import os
from vg_provisioning.python_terraform.terraform import Terraform
from importlib import resources

TF_WORKINGDIR = "vg_provisioning"


def to_absolute_path(path):
    """
    Converts a relative or ~-based path to an absolute path.
    """
    expanded = os.path.expanduser(path)
    return os.path.abspath(expanded)


def get_working_dir(folder_name: str) -> str:
    with resources.path(folder_name, "") as working_dir:
        return str(working_dir)


def get_from_env() -> tuple[str, str]:
    token = os.environ.get("DO_TOKEN", "")
    ssh_key_name = os.environ.get("DO_SSH_KEY_NAME", "")
    return token, ssh_key_name


class DO:
    def __init__(
        self,
        token: str,
        ssh_key_name: str,
        ssh_pub_key_file: str = "~/.ssh/id_rsa.pub",
        tf_working_dir: str = TF_WORKINGDIR,
    ):
        self.token = token
        self.ssh_key_name = ssh_key_name
        self.ssh_pub_key_file = ssh_pub_key_file
        self.tf_session = Terraform(working_dir=tf_working_dir)

    def apply(self):
        # Implementation of tf_apply method
        print(self.tf_session.working_dir)
        ssh_pub_key_file_abs = to_absolute_path(self.ssh_pub_key_file)
        tf_variables = {
            "do_token": self.token,
            "do_ssh_key_name": self.ssh_key_name,
            "do_ssh_pubkey_file": ssh_pub_key_file_abs,
        }
        self.tf_session.__setattr__("variables", tf_variables)
        print("Init and plan before provisioning.......")
        self.tf_session.init()
        self.tf_session.plan()
        print("Server provisioning.......")
        return self.tf_session.apply()
