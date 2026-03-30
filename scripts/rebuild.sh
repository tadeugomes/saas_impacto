#!/usr/bin/env bash
# Rebuild e restart dos serviços backend do SaaS Impacto Portuário.
#
# Uso:
#   ./scripts/rebuild.sh          # rebuild api + worker + beat
#   ./scripts/rebuild.sh api      # rebuild apenas a api
#   ./scripts/rebuild.sh --all    # rebuild todos os serviços (inclui frontend)

set -euo pipefail

cd "$(dirname "$0")/.."

SERVICES="${1:-}"

echo "==> Parando serviços..."

if [ "$SERVICES" = "--all" ]; then
  docker compose down
  echo "==> Rebuild completo (api + worker + beat + frontend)..."
  docker compose build api worker beat frontend
  echo "==> Subindo todos os serviços..."
  docker compose up -d
elif [ -n "$SERVICES" ]; then
  echo "==> Rebuild de: $SERVICES"
  docker compose build "$SERVICES"
  docker compose up -d "$SERVICES"
else
  echo "==> Rebuild backend (api + worker + beat)..."
  docker compose build api worker beat
  docker compose up -d api worker beat
fi

echo "==> Aguardando health check..."
sleep 5

# Health check
if curl -sf http://localhost:8000/health/ready > /dev/null 2>&1; then
  echo "✓ API healthy"
else
  echo "⚠ API não respondeu ao health check — verificar logs com: docker compose logs api"
fi

echo "==> Done!"
