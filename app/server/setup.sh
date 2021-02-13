# 1. SSH into droplet
# 2. Setup user
# 3. Copy ssh key into /home/user/.ssh/authorized_keys
# 4. Login as root

# 5. Setup swap, here for 6GB
fallocate -l 6G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo "/swapfile swap swap defaults 0 0" >> /etc/fstab 

# 6. Setup docker-ce
apt update
apt install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable"
apt update
apt install -y docker-ce
usermod -aG docker jacob

# 7. Firewall setup
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
echo "y" | ufw enable
ufw allow 443

docker run -d \
  --name=swag \
  --cap-add=NET_ADMIN \
  -e PUID=1000 \
  -e PGID=1000 \
  -e TZ=Europe/Berlin \
  -e URL=vesseg.online \
  -e VALIDATION=http \
  -p 443:443 \
  -p 80:80 \
  -v /path/to/appdata/config:/config \
  --restart unless-stopped \
  linuxserver/swag