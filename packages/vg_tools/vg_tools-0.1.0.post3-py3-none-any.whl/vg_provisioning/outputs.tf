#####  PRINTING ALL PUB & PRI IP ADDRESSES
#####

output "pub-ip-serveradmin1" {
 value = digitalocean_droplet.web.ipv4_address
}

# output "pub-ip-serveradmin2" {
#  value = digitalocean_droplet.app.ipv4_address
# }
