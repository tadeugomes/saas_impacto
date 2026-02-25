variable "name" {
  type        = string
  description = "Nome único do bucket."
}

variable "location" {
  type        = string
  description = "Região ou região multi-região."
}

variable "uniform_access" {
  type        = bool
  default     = true
  description = "Acesso uniforme."
}

variable "lifecycle_delete_age" {
  type        = number
  default     = 365
  description = "Dias para remoção automática de versões antigas."
}

resource "google_storage_bucket" "this" {
  name          = var.name
  location      = var.location
  force_destroy = true
  uniform_bucket_level_access = var.uniform_access

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = var.lifecycle_delete_age
    }
  }
}

output "bucket_name" {
  value = google_storage_bucket.this.name
}
