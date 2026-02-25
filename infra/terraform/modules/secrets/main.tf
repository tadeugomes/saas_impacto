variable "project_id" {
  type        = string
  description = "ID do projeto."
}

variable "secrets" {
  type        = map(string)
  sensitive   = true
  default     = {}
  description = "Mapa de segredos (nome -> valor)."
}

resource "google_secret_manager_secret" "this" {
  for_each = var.secrets
  secret_id = each.key
  project   = var.project_id

  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "version" {
  for_each    = var.secrets
  secret      = google_secret_manager_secret.this[each.key].id
  secret_data = each.value
}

output "secret_ids" {
  value = { for k, v in google_secret_manager_secret.this : k => v.id }
  sensitive = true
}
