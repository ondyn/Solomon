#!/bin/sh
set -eu

apt-get update
apt-get install -y apt-transport-https ca-certificates curl docker.io docker-compose gnupg
mkdir -p /usr/local/lib/docker/cli-plugins
curl -fsSL https://github.com/docker/compose/releases/download/v2.29.7/docker-compose-linux-x86_64 -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
if ! command -v gcloud >/dev/null 2>&1; then
	curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
	echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" > /etc/apt/sources.list.d/google-cloud-sdk.list
	apt-get update
	apt-get install -y google-cloud-cli
fi
systemctl enable --now docker
useradd --system --create-home --groups docker solomon || true
mkdir -p /opt/solomon/backups
chown -R solomon:solomon /opt/solomon
touch /var/lib/solomon-ready