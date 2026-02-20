variable "name" {}
variable "location" {}
variable "uniform_access" { default = true }

resource "google_storage_bucket" "this" {
  name          = var.name
  location      = var.location
  force_destroy = true
  uniform_bucket_level_access = var.uniform_access
}

output "bucket_name" {
  value = google_storage_bucket.this.name
}
