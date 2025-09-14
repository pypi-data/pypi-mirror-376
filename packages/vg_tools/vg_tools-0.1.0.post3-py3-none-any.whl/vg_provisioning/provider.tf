# Configure the DigitalOcean Provider

provider "digitalocean" {
  token = var.do_token
}

# SSH KEY
data "digitalocean_ssh_key" "existing" {
  count = var.do_ssh_key_name != "" ? 1 : 0
  name  = var.do_ssh_key_name
}

data "local_file" "ssh_pubkey" {
  count    = var.do_ssh_key_name == "" ? 1 : 0
  filename = var.do_ssh_pubkey_file
}
