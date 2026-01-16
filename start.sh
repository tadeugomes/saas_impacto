#!/bin/bash
# Script para iniciar o ambiente de desenvolvimento local

set -e

echo "🚀 Iniciando ambiente de desenvolvimento SaaS Impacto Portuário"
echo ""

# Diretório do projeto
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

# 1. Verificar Docker
echo "📦 Verificando Docker..."
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker não está rodando. Por favor, inicie o Docker Desktop e execute este script novamente."
    echo ""
    echo "Para iniciar o Docker Desktop no macOS:"
    echo "  1. Abra o Spotlight (Cmd + Espaço)"
    echo "  2. Digite 'Docker' e inicie o Docker Desktop"
    echo "  3. Aguarde o ícone do Docker aparecer na barra de menu"
    echo ""
    exit 1
fi
echo "✅ Docker está rodando"
echo ""

# 2. Iniciar containers PostgreSQL e Redis
echo "🐘 Iniciando PostgreSQL e Redis..."
docker compose up -d postgres redis
echo "✅ Containers iniciados"
echo ""

# 3. Aguardar PostgreSQL ficar pronto
echo "⏳ Aguardando PostgreSQL ficar pronto..."
until docker exec saas_impacto_postgres pg_isready -U postgres >/dev/null 2>&1; do
    echo "   Aguardando PostgreSQL..."
    sleep 2
done
echo "✅ PostgreSQL pronto"
echo ""

# 4. Criar banco se não existir
echo "🔧 Configurando banco de dados..."
docker exec saas_impacto_postgres psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname='saas_impacto'" | grep -q 1 || \
    docker exec saas_impacto_postgres psql -U postgres -c "CREATE DATABASE saas_impacto;"
echo "✅ Banco de dados configurado"
echo ""

# 5. Verificar/installar dependências Python
echo "📦 Verificando dependências Python..."
if [ ! -d "venv" ]; then
    echo "   Criando virtual environment..."
    python3 -m venv venv
fi
echo "✅ Virtual environment criado"
echo ""

# 6. Instalar/Atualizar pacotes
echo "📥 Instalando pacotes Python..."
source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r backend/requirements.txt
echo "✅ Pacotes instalados"
echo ""

# 7. Executar migrations
echo "🗄️  Executando migrations..."
cd backend
export PYTHONPATH="${PYTHONPATH}:${PROJECT_ROOT}/backend"
alembic upgrade head || echo "⚠️  Migrations podem já ter sido executadas"
echo "✅ Migrations executadas"
cd ..
echo ""

# 8. Criar usuário admin de teste
echo "👤 Criando usuário de teste..."
docker exec saas_impacto_postgres psql -U postgres -d saas_impacto -c "
INSERT INTO tenants (id, nome, slug, ativo)
VALUES ('00000000-0000-0000-0000-000000000001', 'Tenant Demo', 'demo', true)
ON CONFLICT (id) DO NOTHING;

INSERT INTO users (id, tenant_id, email, nome, hashed_password, ativo, roles)
VALUES ('00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', 'admin@saas.local',
        'Administrador', '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOOzSlWxtQjOWuwFqr8WOdeYQZ3kCrNQ2', true, ARRAY['admin']::text[])
ON CONFLICT (id) DO NOTHING;
" 2>/dev/null || echo "   Usuário de teste já existe"
echo "   Usuário: admin@saas.local"
echo "   Senha: admin123"
echo ""

# 9. Informações de acesso
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Ambiente configurado com sucesso!"
echo ""
echo "📌 Serviços disponíveis:"
echo "   • PostgreSQL: localhost:5432"
echo "   • Redis: localhost:6379"
echo "   • PgAdmin: http://localhost:5050 (se habilitado)"
echo ""
echo "📌 Para iniciar o servidor API:"
echo "   cd backend"
echo "   source ../venv/bin/activate"
echo "   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "📌 API Docs disponíveis em:"
echo "   • http://localhost:8000/docs (Swagger UI)"
echo "   • http://localhost:8000/redoc (ReDoc)"
echo ""
echo "📌 Credenciais de teste:"
echo "   • Email: admin@saas.local"
echo "   • Senha: admin123"
echo ""
echo "📌 Para parar os containers:"
echo "   docker compose down"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
