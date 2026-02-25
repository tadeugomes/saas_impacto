terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

locals {
  common_services = [
    "compute.googleapis.com",
    "vpcaccess.googleapis.com",
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "redis.googleapis.com",
    "secretmanager.googleapis.com",
    "servicenetworking.googleapis.com",
    "bigquery.googleapis.com",
    "storage.googleapis.com",
  ]

  api_env_vars = {
    STAGE        = "production"
    ENVIRONMENT  = "production"
    POSTGRES_HOST = module.cloud_sql.private_ip_address
    POSTGRES_PORT = "5432"
    POSTGRES_DB   = "saas_impacto_prod"
    POSTGRES_USER = "postgres"
    REDIS_HOST    = module.redis.host
    REDIS_PORT    = tostring(module.redis.port)
    REDIS_DB      = "0"
    GOOGLE_APPLICATION_CREDENTIALS = ""
    GCP_PROJECT_ID = var.project_id
    BQ_DATASET_ANTAQ = "antaqdados.br_antaq_estatistico_aquaviario"
    BQ_DATASET_MARTS = "marts_impacto"
  }

  worker_env_vars = merge(local.api_env_vars, {
    STAGE = "production"
    ENVIRONMENT = "production"
  })

  secret_env_vars = {
    POSTGRES_PASSWORD = try(module.secrets.secret_ids["POSTGRES_PASSWORD"], null)
    REDIS_PASSWORD    = try(module.secrets.secret_ids["REDIS_PASSWORD"], null)
    DATABASE_URL      = try(module.secrets.secret_ids["DATABASE_URL"], null)
    REDIS_URL         = try(module.secrets.secret_ids["REDIS_URL"], null)
    JWT_SECRET_KEY    = try(module.secrets.secret_ids["JWT_SECRET_KEY"], null)
    JWT_SECRET        = try(module.secrets.secret_ids["JWT_SECRET"], null)
    GCP_SA_KEY       = try(module.secrets.secret_ids["GCP_SA_KEY"], null)
  }
  filtered_secret_env_vars = {
    for secret_name, secret_id in local.secret_env_vars :
    secret_name => secret_id
    if secret_id != null
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_project_service" "required_services" {
  for_each = toset(local.common_services)

  project = var.project_id
  service = each.value

  disable_dependent_services = false
}

module "vpc" {
  source      = "../../modules/vpc"
  name        = "${var.env_prefix}-vpc"
  region      = var.region
  project_id  = var.project_id

  depends_on = [google_project_service.required_services]
}

module "secrets" {
  source     = "../../modules/secrets"
  project_id = var.project_id
  secrets    = var.secrets

  depends_on = [google_project_service.required_services]
}

module "storage" {
  source   = "../../modules/storage"
  name     = "${var.env_prefix}-reports"
  location = var.region
}

module "iam" {
  source      = "../../modules/iam"
  project_id  = var.project_id
  name_prefix = var.env_prefix
}

module "cloud_sql" {
  source            = "../../modules/cloud_sql"
  name              = "${var.env_prefix}-postgres"
  region            = var.region
  database_name     = "saas_impacto_${var.env_prefix}"
  database_user     = "postgres"
  database_password = var.database_password
  vpc_self_link     = module.vpc.vpc_self_link

  depends_on = [module.vpc]
}

module "redis" {
  source     = "../../modules/memorystore"
  name       = "${var.env_prefix}-redis"
  region     = var.region
}

module "api" {
  source               = "../../modules/cloud_run"
  name                 = "${var.env_prefix}-api"
  region               = var.region
  image                = var.api_image
  container_port       = 8000
  memory               = "2Gi"
  cpu                  = "2000m"
  min_instances        = 1
  max_instances        = 5
  service_account_email = module.iam.api_service_account_email
  env_vars             = local.api_env_vars
  secret_env_vars      = local.filtered_secret_env_vars
  vpc_connector        = module.vpc.connector_full_name

  depends_on = [module.cloud_sql, module.redis, module.iam, module.secrets, module.vpc]
}

module "worker" {
  source               = "../../modules/cloud_run"
  name                 = "${var.env_prefix}-worker"
  region               = var.region
  image                = var.worker_image
  container_port       = 8000
  memory               = "4Gi"
  cpu                  = "2000m"
  min_instances        = 1
  max_instances        = 2
  service_account_email = module.iam.worker_service_account_email
  env_vars             = local.worker_env_vars
  secret_env_vars      = local.filtered_secret_env_vars
  vpc_connector        = module.vpc.connector_full_name

  depends_on = [module.cloud_sql, module.redis, module.iam, module.secrets, module.vpc]
}

output "api_service_url" {
  value       = module.api.service_url
  description = "URL pública do serviço de API."
}

output "worker_service_name" {
  value       = module.worker.service_id
  description = "Nome do serviço worker."
}

output "database_private_ip" {
  value       = module.cloud_sql.private_ip_address
  description = "IP privado do PostgreSQL."
}

output "redis_host" {
  value       = module.redis.host
  description = "Endpoint do Memorystore."
}
