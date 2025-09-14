#### Create a new server with public key

resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

resource "digitalocean_ssh_key" "ssh_key" {
  count      = var.do_ssh_key_name == "" ? 1 : 0
  name       = "roy-serveradmin-key-${random_string.suffix.result}"
  public_key = data.local_file.ssh_pubkey[0].content
}

# Create a new Web Droplet in the sg region
resource "digitalocean_droplet" "web" {
  image  = "ubuntu-24-04-x64"
  name   = "roy-serveradmin-web-${random_string.suffix.result}"
  region = "sgp1"
  size   = "s-1vcpu-512mb-10gb"
  #ssh_keys = [data.digitalocean_ssh_key.ssh_key.id]
  ssh_keys = [
    var.do_ssh_key_name != "" ? data.digitalocean_ssh_key.existing[0].id : digitalocean_ssh_key.ssh_key[0].id
  ]
}

# resource "digitalocean_droplet" "app" {
#   image  = "ubuntu-22-04-x64"
#   name   = "roy-serveradmin-app"
#   region = "sgp1"
#   size   = "s-1vcpu-512mb-10gb"
#   ssh_keys = [data.digitalocean_ssh_key.ssh_key.id]
# }
