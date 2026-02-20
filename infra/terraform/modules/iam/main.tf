variable "name_prefix" {
  type        = string
  description = "Prefixo para nomes das service accounts."
}

variable "project_id" {
  type        = string
  description = "ID do projeto GCP."
}

variable "extra_roles" {
  type        = map(list(string))
  default     = {}
  description = "Mapeamento opcional de roles por service account."
}

resource "google_service_account" "api" {
  account_id   = "${var.name_prefix}-api"
  display_name = "SaaS Impacto API service account"
}

resource "google_service_account" "worker" {
  account_id   = "${var.name_prefix}-worker"
  display_name = "SaaS Impacto Worker service account"
}

locals {
  default_roles = {
    api = [
      "roles/secretmanager.secretAccessor",
      "roles/run.invoker",
      "roles/bigquery.user",
      "roles/storage.objectViewer",
    ]
    worker = [
      "roles/secretmanager.secretAccessor",
      "roles/bigquery.user",
      "roles/storage.objectAdmin",
      "roles/cloudsql.client",
      "roles/redis.editor",
    ]
  }

  extra_api_roles = concat(
    local.default_roles.api,
    lookup(var.extra_roles, "api", [])
  )
  extra_worker_roles = concat(
    local.default_roles.worker,
    lookup(var.extra_roles, "worker", [])
  )
}

resource "google_project_iam_member" "secrets_reader" {
  for_each = {
    for role in local.extra_api_roles :
    "api-${replace(role, "/", "-")}" => {
      sa   = google_service_account.api.email
      role = role
    }
  }

  project = var.project_id
  role    = each.value.role
  member  = "serviceAccount:${each.value.sa}"
}

resource "google_project_iam_member" "worker_roles" {
  for_each = {
    for role in local.extra_worker_roles :
    "worker-${replace(role, "/", "-")}" => {
      sa   = google_service_account.worker.email
      role = role
    }
  }

  role   = each.value.role
  member = "serviceAccount:${each.value.sa}"
  project = var.project_id
}

output "api_service_account_email" {
  value = google_service_account.api.email
}

output "worker_service_account_email" {
  value = google_service_account.worker.email
}
