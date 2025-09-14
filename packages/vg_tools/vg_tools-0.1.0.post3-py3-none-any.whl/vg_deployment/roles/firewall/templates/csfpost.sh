#!/bin/bash
/sbin/iptables -F FORWARD
/sbin/iptables -P FORWARD ACCEPT

#/sbin/iptables -I INPUT -i eth0 -d 224.0.0.0/8 -p vrrp -j ACCEPT
#/sbin/iptables -I OUTPUT -o eth0 -d 224.0.0.0/8 -p vrrp -j ACCEPT

#/sbin/iptables -t mangle -F
#/sbin/iptables -t mangle -X
#/sbin/iptables -t mangle -A PREROUTING -i eth0 -m ttl --ttl-gt 100 -j DROP
#/sbin/iptables -t mangle -A PREROUTING -i eth0 -m ttl --ttl-lt 59 -j DROP

##/sbin/iptables -t mangle -A PREROUTING -i eth0 -m ttl --ttl-eq 100 -j DROP
##iptables -t mangle -A PREROUTING -i eth0 -m ttl --ttl-eq 243 -j DROP
