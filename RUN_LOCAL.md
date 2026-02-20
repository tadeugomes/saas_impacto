# 🚀 Guia de Execução Local

## Pré-requisitos

- Python 3.11+
- Docker e Docker Compose (opcional, recomendado)
- PostgreSQL 16+ (se não usar Docker)
- Redis 7+ (se não usar Docker)

## Opção 1: Usando Docker (Recomendado)

### 1. Iniciar Docker Desktop

Abra o Docker Desktop no macOS.

### 2. Executar o script de setup

```bash
cd /Users/tgt/Documents/GitHub/saas_impacto
./start.sh
```

Este script vai:
- Iniciar containers PostgreSQL e Redis
- Criar virtual environment Python
- Instalar dependências
- Executar migrations
- Criar usuário de teste

### 3. Iniciar o servidor API

```bash
cd backend
source ../venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Acessar

- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **PgAdmin** (se habilitado): http://localhost:5050

## Opção 2: Sem Docker (PostgreSQL/Redis nativos)

### 1. Instalar PostgreSQL e Redis

```bash
# macOS com Homebrew
brew install postgresql@16 redis
brew services start postgresql@16
brew services start redis
```

### 2. Criar banco de dados

```bash
psql postgres -c "CREATE DATABASE saas_impacto;"
```

### 3. Criar virtual environment e instalar dependências

```bash
cd /Users/tgt/Documents/GitHub/saas_impacto
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

### 4. Executar migrations

```bash
cd backend
export PYTHONPATH="${PYTHONPATH}:/Users/tgt/Documents/GitHub/saas_impacto/backend"
alembic upgrade head
```

### 5. Criar usuário de teste

```bash
psql saas_impacto << 'EOF'
INSERT INTO tenants (id, nome, slug, ativo)
VALUES ('00000000-0000-0000-0000-000000000001', 'Tenant Demo', 'demo', true)
ON CONFLICT (id) DO NOTHING;

INSERT INTO users (id, tenant_id, email, nome, hashed_password, ativo, roles)
VALUES ('00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', 'admin@saas.local',
        'Administrador', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOOzSlWxtQjOWuwFqr8WOdeYQZ3kCrNQ2', true, ARRAY['admin']::text[])
ON CONFLICT (id) DO NOTHING;
EOF
```

### 6. Configurar .env

Edite `backend/.env` e ajuste as variáveis se necessário.

### 7. Iniciar o servidor

```bash
cd backend
source ../venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Credenciais de Teste

```
Email: admin@saas.local
Senha: admin123
```

## Testando a API

### 1. Login e obter token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@saas.local", "password": "admin123"}'
```

### 2. Consultar metadados dos indicadores

```bash
curl "http://localhost:8000/api/v1/indicators/metadata"
```

### 3. Consultar um indicador específico

```bash
# IND-5.02: PIB per Capita
curl -X POST "http://localhost:8000/api/v1/indicators/query" \
  -H "Content-Type: application/json" \
  -d '{
    "codigo_indicador": "IND-5.02",
    "id_municipio": "3550308",
    "ano": 2022
  }'

### 4. Validação completa do Módulo 5 (BigQuery)

```bash
cd /Users/tgt/Documents/GitHub/saas_impacto
source venv/bin/activate

# Regenera os marts e metadados do Módulo 5 antes da validação
PYTHONPATH=/Users/tgt/Documents/GitHub/saas_impacto/backend \
python -m scripts.build_module5_marts --versao-pipeline v1.0.2

# Executa validação de ponta a ponta do Módulo 5 com dados reais
python testar_modulo5_dados_reais.py
```
```

## Comandos Úteis

```bash
# Ver logs dos containers
docker compose logs -f postgres

# Parar containers
docker compose down

# Ver status dos containers
docker compose ps

# Entrar no PostgreSQL
docker exec -it saas_impacto_postgres psql -U postgres saas_impacto

# Ver tabelas
psql saas_impacto -c "\dt"
```

## Estrutura do Projeto

```
saas_impacto/
├── backend/
│   ├── app/
│   │   ├── api/v1/        # Endpoints API
│   │   ├── db/            # Banco de dados e BigQuery
│   │   ├── services/      # Lógica de negócio
│   │   ├── schemas/       # Schemas Pydantic
│   │   └── main.py        # Aplicação FastAPI
│   ├── .env                # Variáveis de ambiente
│   └── requirements.txt
├── docker-compose.yml
└── start.sh               # Script de setup
```

## Solução de Problemas

### PostgreSQL não conecta

```bash
# Verificar se PostgreSQL está rodando
docker ps | grep postgres

# Ou sem Docker
brew services list | grep postgresql
```

### Erro de import Python

```bash
# Certifique-se de estar no diretório correto
cd /Users/tgt/Documents/GitHub/saas_impacto/backend

# Ativar virtual environment
source ../venv/bin/activate

# Verificar PYTHONPATH
echo $PYTHONPATH
export PYTHONPATH="/Users/tgt/Documents/GitHub/saas_impacto/backend:$PYTHONPATH"
```

### Porta já em uso

```bash
# Ver processo na porta 8000
lsof -i :8000

# Matar processo
kill -9 <PID>
```
