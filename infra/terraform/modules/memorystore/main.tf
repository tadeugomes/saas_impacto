variable "name" {}
variable "region" {}
variable "memory_size_gb" { default = 1 }
variable "tier" { default = "BASIC" }

resource "google_redis_instance" "this" {
  name           = var.name
  tier           = var.tier
  memory_size_gb = var.memory_size_gb
  region         = var.region
}

output "host" {
  value = google_redis_instance.this.host
}

output "port" {
  value = google_redis_instance.this.port
}
