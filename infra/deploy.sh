#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

REGIAO="$(terraform output -raw -state=terraform.tfstate 2>/dev/null; echo)"
ECR_URL="$(terraform output -raw ecr_repository_url)"
REGIAO="$(echo "$ECR_URL" | cut -d. -f4)"
TAG="${1:-latest}"

echo "==> Login no ECR ($REGIAO)"
aws ecr get-login-password --region "$REGIAO" \
  | docker login --username AWS --password-stdin "${ECR_URL%%/*}"

echo "==> Build da imagem"
docker build -t "$ECR_URL:$TAG" ..

echo "==> Push da imagem"
docker push "$ECR_URL:$TAG"

echo "==> Imagem publicada: $ECR_URL:$TAG"
echo "    O App Runner fara o deploy automatico (auto_deployments_enabled)."
