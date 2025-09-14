import logging

from args.args import parse_args
from utils.utils import DO, get_from_env, get_working_dir
from vg_deployment.python_ansible.ansible import (
    AnsiblePlaybook,
    construct_inventory,
)

ANSIBLE_WORKDIR = "vg_deployment"
ANSIBLE_INV_FILE_NAME = "inventory.ini"
ANSIBLE_PLAYBOOK_FILE_NAME = "site.yml"
# ANSIBLE_INV_FILE = f"{ANSIBLE_WORKDIR}/{ANSIBLE_INV_FILE_NAME}"
TF_WORKINGDIR = "vg_provisioning"


def vg_deploy():
    args = parse_args()
    logging.basicConfig(
        level=args.log_level,  # Change to logging.INFO or another level as needed
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if args.provisioned_ip:
        output_ips = args.provisioned_ip
        logging.info(
            f"Using provided IPs, all the privisioning steps skip!: {output_ips}"
        )
        manual_install = True
    else:
        (
            token,
            key,
        ) = get_from_env()
        tf_working_dir = get_working_dir(TF_WORKINGDIR)
        do_tf_session = DO(
            token=token,
            ssh_key_name=key,
            ssh_pub_key_file=args.ssh_pub_key_file,
            tf_working_dir=tf_working_dir,
        )
        do_tf_session.apply()
        output_ips = do_tf_session.tf_session.output()
        manual_install = False

    ansible_extra_vars = {"php_version": args.php_version}
    ansible_working_dir = get_working_dir(ANSIBLE_WORKDIR)
    ansible_inv_file = f"{ansible_working_dir}/{ANSIBLE_INV_FILE_NAME}"

    construct_inventory(output_ips, ansible_inv_file)

    ansible_playbook_session = AnsiblePlaybook(
        inventory=ANSIBLE_INV_FILE_NAME,
        playbook=ANSIBLE_PLAYBOOK_FILE_NAME,
        working_dir=ansible_working_dir,
        private_key_file=args.ssh_key_file,
        ssh_user=args.ssh_user,
        ssh_password=args.ssh_password,
    )

    out, err = ansible_playbook_session.run(
        extra_vars=ansible_extra_vars, manual_install=manual_install
    )

    print(out)
    if err:
        print(err)


if __name__ == "__main__":
    vg_deploy()
