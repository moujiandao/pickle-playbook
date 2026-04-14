#!/usr/bin/env bash
set -euo pipefail
EC2_HOST="${EC2_HOST:-ec2-user@your-ec2-host}"
ssh "$EC2_HOST" "cd ~/pickle-playbook && git pull && docker compose -f docker-compose.pickle.yml up -d --build"
echo "Health check..."
sleep 3
curl -f "http://${EC2_HOST#*@}:8001/health" || echo "Health check failed - check EC2 logs"
