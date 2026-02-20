# SaaS Impacto Portuário

Sistema multi-tenant para análise do impacto econômico do setor portuário brasileiro.

## Stack Tecnológica

- **Backend:** FastAPI (Python 3.10+)
- **Banco Operacional:** PostgreSQL + SQLAlchemy (async)
- **Data Warehouse:** Google BigQuery
- **Cache/Queue:** Redis
- **Autenticação:** JWT + OAuth2

## Status da Implementação

### ✅ FASE 1 - Fundação (COMPLETA)

- [x] Estrutura de pastas criada
- [x] Configurações Pydantic (config.py)
- [x] PostgreSQL schema com RLS (init_db.sql)
- [x] Modelos SQLAlchemy (Tenant, User, DashboardView)
- [x] Alembic migrations configurado
- [x] JWT auth implementado
- [x] Endpoints `/login`, `/register`
- [x] Middleware de multi-tenancy

### 🔄 FASE 2 - BigQuery (EM PROGRESSO)

- [ ] Mart materializado ship_operations
- [ ] Queries Módulo 1
- [ ] Cliente BigQuery

## Setup Rápido

### 1. Criar ambiente virtual

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar variáveis de ambiente

```bash
cp .env.example .env
# Editar .env com suas configurações
```

Variáveis obrigatórias:
```bash
SECRET_KEY=seu-secret-key-aqui
JWT_SECRET_KEY=seu-jwt-secret-aqui
POSTGRES_PASSWORD=sua-senha
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

### 4. Inicializar PostgreSQL

```bash
psql -U postgres -c "CREATE DATABASE saas_impacto;"
psql -U postgres -d saas_impacto -f ../scripts/init_db.sql
```

### 5. Executar migrations Alembic

```bash
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

### 6. Rodar servidor

```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Acessar:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

## Testar API

### Registrar novo usuário

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@exemplo.com",
    "password": "admin123",
    "nome": "Admin",
    "tenant_slug": "organizacao-exemplo"
  }'
```

### Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@exemplo.com",
    "password": "admin123"
  }'
```

Resposta:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### Acessar endpoint protegido

```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer eyr..." \
  -H "X-Tenant-ID: uuid-do-tenant"

### Validação do Módulo 5 com dados reais (BigQuery)

Fluxo recomendado para validar contratos e execução do Módulo 5 com dados reais:

```bash
cd /Users/tgt/Documents/GitHub/saas_impacto
source venv/bin/activate

# Atualiza marts (crosswalk, mart econômico, metadata)
PYTHONPATH=/Users/tgt/Documents/GitHub/saas_impacto/backend \
python -m scripts.build_module5_marts --versao-pipeline v1.0.2

# Executa o script de validação ponta a ponta do Módulo 5
python testar_modulo5_dados_reais.py
```

Observação: se rodar em outro workspace, troque os caminhos absolutos pelo seu caminho local.
```

## Estrutura do Projeto

```
saas_impacto/
├── backend/
│   ├── app/
│   │   ├── api/v1/       # Endpoints REST
│   │   ├── core/         # Security, tenant
│   │   ├── db/           # Models, BigQuery
│   │   ├── schemas/      # Pydantic
│   │   ├── services/     # Business logic
│   │   └── main.py       # FastAPI app
│   ├── alembic/          # Migrations
│   ├── scripts/          # SQL, utils
│   └── requirements.txt
└── planejamento/docs/    # Documentação técnica
```

## Próximos Passos

1. Implementar mart materializado no BigQuery
2. Criar queries para Módulo 1 (12 indicadores)
3. Implementar endpoints de indicadores
4. Desenvolver frontend Vue/React

## Documentação

- [Especificação Técnica](planejamento/docs/INDICADORES_ESPECIFICACAO_TECNICA.md)
- [Padrões SQL ANTAQ](planejamento/docs/role_sql_antaq_bigquery/INSTRUCOES_UNIFICADAS_SQL_ANTAQ.md)
- [Plano de Implementação](.claude/plans/gentle-questing-llama.md)
- [Guia de Interpretação — Módulo 5](docs/guia_interpretacao_modulo5.md)
