# Deployment: Ansible playbook warpper which will install and configure LAMP stack to your server.

**Recommended to use vg_tools.py instead of direct run this playbook**

**In case you want to test and verify tasks in the playbook, follow this Manual Installation**

You need to input target servers into hosts file `inventory.ini` before you start the command.

```bash
cd vg_deployment
## Using password for ssh connction
ANSIBLE_SSH_PASSWORD=<your_server_password> ANSIBLE_SSH_USER=root ansible-playbook -i inventory.ini site.yml
## Or using ssh key
ANSIBLE_PRIVATE_KEY_FILE=<path_to_private_key> ansible-playbook -i inventory.ini site.yml
```

The process needs 10 minutes to be completed
