terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

module "vpc" {
  source     = "../../modules/vpc"
  name       = "${var.env_prefix}-vpc"
  region     = var.region
  project_id = var.project_id
}

module "secrets" {
  source     = "../../modules/secrets"
  project_id = var.project_id
  secrets    = var.secrets
}

module "storage" {
  source   = "../../modules/storage"
  name     = "${var.env_prefix}-reports"
  location = var.region
}

module "iam" {
  source     = "../../modules/iam"
  project_id = var.project_id
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
}

module "redis" {
  source = "../../modules/memorystore"
  name   = "${var.env_prefix}-redis"
  region = var.region
}

module "api" {
  source              = "../../modules/cloud_run"
  name                = "${var.env_prefix}-api"
  region              = var.region
  image               = var.api_image
  container_port      = 8000
  memory              = "1Gi"
  cpu                 = "1"
  min_instances       = 0
  max_instances       = 2
  service_account_email = module.iam.api_service_account_email
  env_vars            = {
    STAGE = "staging"
  }
}

module "worker" {
  source              = "../../modules/cloud_run"
  name                = "${var.env_prefix}-worker"
  region              = var.region
  image               = var.worker_image
  container_port      = 8000
  memory              = "2Gi"
  cpu                 = "2"
  min_instances       = 0
  max_instances       = 1
  service_account_email = module.iam.worker_service_account_email
  env_vars            = {
    STAGE = "staging"
  }
}
