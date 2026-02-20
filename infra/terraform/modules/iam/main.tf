variable "name_prefix" {}
variable "project_id" {}

resource "google_service_account" "api" {
  account_id   = "${var.name_prefix}-api"
  display_name = "SaaS Impacto API service account"
}

resource "google_service_account" "worker" {
  account_id   = "${var.name_prefix}-worker"
  display_name = "SaaS Impacto Worker service account"
}

resource "google_project_iam_member" "secrets_reader" {
  for_each = toset([
    google_service_account.api.email,
    google_service_account.worker.email,
  ])

  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${each.key}"
}

output "api_service_account_email" {
  value = google_service_account.api.email
}

output "worker_service_account_email" {
  value = google_service_account.worker.email
}
