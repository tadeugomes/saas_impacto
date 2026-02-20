# Terraform - Infraestrutura como Código (IaC)

Esta pasta contém a stack da plataforma no Terraform com módulos reutilizáveis e
ambientes `staging` e `production`.

## Estrutura

- `modules/*`: módulos do Google Cloud usados pelo projeto
  - `cloud_run`: API e worker
  - `cloud_sql`: PostgreSQL 16
  - `memorystore`: Redis 7
  - `storage`: bucket GCS para relatórios/artifacts
  - `secrets`: Secret Manager
  - `iam`: service accounts com permissões mínimas
  - `vpc`: VPC privada, Cloud NAT e connector para Cloud Run
- `environments/staging`: configuração de staging
- `environments/production`: configuração de produção
- `backend.tf`: backend remoto em GCS

## Backend remoto

Edite `backend.tf` com o bucket de estado:

```hcl
terraform {
  backend "gcs" {
    bucket = "saas-impacto-tfstate"
    prefix = "terraform/state"
  }
}
```

## Pré-requisitos

- Projeto GCP com billing habilitado
- Conta de serviço de administração do projeto
- Bucket GCS para estado (`TF_STATE_BUCKET` no CI)

## Bootstrap

Defina `terraform.tfvars` por ambiente sem segredos versionados no repositório:

```bash
cd infra/terraform/environments/staging

cat > terraform.tfvars <<EOF
project_id       = "seu-projeto"
region           = "southamerica-east1"
api_image        = "southamerica-east1-docker.pkg.dev/seu-projeto/saas-impacto/api:sha"
worker_image     = "southamerica-east1-docker.pkg.dev/seu-projeto/saas-impacto/worker:sha"
database_password = "troque-por-uma-senha-forte"
secrets = {
  POSTGRES_PASSWORD = "troque-por-uma-senha-forte"
  JWT_SECRET_KEY    = "sua-chave-jwt"
  GCP_SA_KEY       = "json-da-service-account"
}
EOF

terraform init
terraform plan
terraform apply
```

## Workflow

- PR: `terraform plan` em `staging` com comentário automático no PR
- Merge em `main`: `terraform apply` automático em `staging`
- Manual: `workflow_dispatch` para `production` ou `staging` via input `apply_environment`
