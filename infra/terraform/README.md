# Terraform - Infraestrutura como Código (IaC)

Esta pasta contém um esqueleto operacional para manter a stack do projeto
em Terraform. A estrutura segue uma organização simples:

- `modules/*`: módulos reutilizáveis por serviço (Cloud Run, Cloud SQL, Redis, etc.).
- `environments/staging`: configuração alvo para ambiente de staging.
- `environments/production`: configuração alvo para produção.
- `backend.tf`: estado remoto no GCS.

## Estado remoto

Crie um bucket de estado em GCP e ajuste `backend.tf` com:

- `bucket` (ex.: `saas-impacto-tfstate`)
- `prefix` (`terraform/state`)

## Bootstrap rápido

```bash
cd infra/terraform/environments/staging
terraform init
terraform plan
terraform apply
```
